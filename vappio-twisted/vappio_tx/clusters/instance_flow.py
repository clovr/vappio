import os

from twisted.internet import defer

from twisted.python import log

from igs.utils import config
from igs.utils import functional as func
from igs.utils import auth_token

from igs_tx.utils import defer_utils
from igs_tx.utils import global_state
from igs_tx.utils import ssh

from vappio.tasks import task

from vappio.instance import config as vappio_config

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.www_client import clusters as clusters_client_www

class Error(Exception):
    pass

class InstanceStartError(Error):
    pass

## Functions using ensureInstances can
## return this to force an instance into
## the failed collection
FAILED_INSTANCE = 'failed_instance'

RUN_INSTANCE_TRIES = 4

WAIT_FOR_STATE_TRIES = 50

WAIT_FOR_SSH_TRIES = 10

WAIT_FOR_BOOT_TRIES = 360

WAIT_FOR_SERVICES_TRIES = 3

@defer_utils.timeIt
@defer.inlineCallbacks
def startMaster(state, credClient, taskName, cluster):
    @defer.inlineCallbacks
    def _saveCluster(instances):
        instances = yield credClient.updateInstances(instances)
        cl = yield state.persistManager.loadCluster(cluster.clusterName,
                                                    cluster.userName)

        cl = cl.setMaster(instances[0])
        yield state.persistManager.saveCluster(cl)
        defer.returnValue(func.Record(succeeded=instances,
                                      failed=[]))

    credConfigMap = yield credClient.credentialConfig()
    credConfig = config.configFromMap(credConfigMap)
    baseConf = config.configFromConfig(cluster.config,
                                       base=credConfig)
    clusterConf = config.configFromMap({'general.ctype': credConfig('general.ctype'),
                                        'cluster.cluster_public_key': '/mnt/keys/devel1.pem.pub'},
                                       base=baseConf)
    cl = cluster.update(config=clusterConf)

    mode = [vappio_config.MASTER_NODE]
    masterConfFilename = '/tmp/machine.' + global_state.make_ref() + '.conf'
    masterConf = vappio_config.createDataFile(cl.config,
                                              mode,
                                              outFile=masterConfFilename)
    dataFile = vappio_config.createMasterDataFile(cl, masterConf)

    groups = [g.strip()
              for g in cl.config('cluster.master_groups').split(',')]
    masterInstanceList = yield runInstances(credClient,
                                            cl.config('cluster.ami'),
                                            cl.config('cluster.key'),
                                            cl.config('cluster.master_type'),
                                            groups,
                                            cl.config('cluster.availability_zone',
                                                      default=None),
                                            cl.config('cluster.master_bid_price',
                                                      default=None),
                                            1,
                                            1,
                                            open(dataFile).read())

    cl = cl.setMaster(masterInstanceList[0])
    yield state.persistManager.saveCluster(cl)

    os.remove(masterConf)
    os.remove(dataFile)

    instances = yield waitForInstances(masterInstanceList,
                                       [updateTask(taskName,
                                                   'Waiting for master'),
                                        waitForState(credClient,
                                                     'running',
                                                     WAIT_FOR_STATE_TRIES),
                                        _saveCluster,
                                        updateTask(taskName,
                                                   'Master in running state'),
                                        waitForSSH(cl.config('ssh.user'),
                                                   cl.config('ssh.options'),
                                                   WAIT_FOR_SSH_TRIES),
                                        _saveCluster,
                                        updateTask(taskName,
                                                   'SSH up'),
                                        waitForBoot('/tmp/startup_complete',
                                                    cl.config('ssh.user'),
                                                    cl.config('ssh.options'),
                                                    WAIT_FOR_BOOT_TRIES),
                                        _saveCluster,
                                        updateTask(taskName,
                                                   'Booted'),
                                        waitForClusterInfo('local',
                                                           'guest',
                                                           WAIT_FOR_SERVICES_TRIES),
                                        _saveCluster,
                                        updateTask(taskName,
                                                   'Cluster info responded')])

    yield credClient.terminateInstances(instances.failed)
    
    if not instances.succeeded:
        raise Error('Master failed to start')

    cl = yield state.persistManager.loadCluster(cl.clusterName,
                                                cl.userName)

    cl = cl.setState(cl.RUNNING)
    yield state.persistManager.saveCluster(cl)
    
    defer.returnValue(cl)

@defer.inlineCallbacks
def startExecs(state, credClient, taskName, numExec, execType, cluster):
    @defer.inlineCallbacks
    def _saveCluster(instances):
        instances = yield credClient.updateInstances(instances)
        cl = yield state.persistManager.loadCluster(cluster.clusterName,
                                                    cluster.userName)
        cl = cl.addExecNodes(instances)
        yield state.persistManager.saveCluster(cl)
        defer.returnValue(func.Record(succeeded=instances,
                                      failed=[]))
    

    dataFile = vappio_config.createExecDataFile(cluster.config,
                                                cluster.master,
                                                '/tmp/machine.conf')
    

    groups = [g.strip()
              for g in cluster.config('cluster.exec_groups').split(',')]
    execType = cluster.config('cluster.exec_type') if execType is None else execType
    execInstances = yield runInstances(credClient,
                                       cluster.config('cluster.ami'),
                                       cluster.config('cluster.key'),
                                       execType,
                                       groups,
                                       cluster.config('cluster.availability_zone',
                                                      default=None),
                                       cluster.config('cluster.master_bid_price',
                                                      default=None),
                                       numExec,
                                       numExec,
                                       open(dataFile).read())
    
    os.remove(dataFile)

    instances = yield waitForInstances(execInstances,
                                       [updateTask(taskName,
                                                   'Waiting for instances'),
                                        waitForState(credClient,
                                                     'running',
                                                     WAIT_FOR_STATE_TRIES),
                                        _saveCluster,
                                        updateTask(taskName,
                                                   'Instances in running state'),
                                        waitForSSH(cluster.config('ssh.user'),
                                                   cluster.config('ssh.options'),
                                                   WAIT_FOR_SSH_TRIES),
                                        _saveCluster,
                                        updateTask(taskName,
                                                   'SSH up'),
                                        waitForBoot('/tmp/startup_complete',
                                                    cluster.config('ssh.user'),
                                                    cluster.config('ssh.options'),
                                                    WAIT_FOR_BOOT_TRIES),
                                        _saveCluster,
                                        updateTask(taskName,
                                                   'Instance booted')])

    yield credClient.terminateInstances(instances.failed)

    cl = yield state.persistManager.loadCluster(cluster.clusterName,
                                                cluster.userName)

    cl = cl.addExecNodes(instances.succeeded)
    cl = cl.removeExecNodes(instances.failed)

    yield state.persistManager.saveCluster(cl)

    defer.returnValue(cl)
    
@defer.inlineCallbacks
def importCluster(state, credClient, taskName, remoteHost, srcCluster, cluster):
    """Handles retrieving metadata from the remote host and running through
    a battery of tests to ensure that the VM being imported is in a running 
    state and reachable.
    
    """
    @defer.inlineCallbacks
    def _saveCluster(instances):
        instances = yield credClient.updateInstances(instances)
        cl = yield state.persistManager.loadCluster(cluster.clusterName,
                                                    cluster.userName)

        cl = cl.setMaster(instances[0])
        yield state.persistManager.saveCluster(cl)
        defer.returnValue(func.Record(succeeded=instances,
                                      failed=[]))
    
    authToken = auth_token.generateToken(cluster.config('cluster.cluster_public_key'))
    remoteClusters = yield clusters_client_www.listClusters(remoteHost,
                                                            {'cluster_name': srcCluster},
                                                            cluster.userName,
                                                            authToken)
    remoteCluster = remoteClusters[0]

    if remoteCluster.get('state') in ['terminated', 'failed']:
        raise Error('Imported cluster in TERMINATED or FAILED state')

    # If we are importing a local cluster the public and private DNS will 
    # not be valid hostnames that we can query. Need to set them to the 
    # remote host provided in the import-clusters call
    if 'clovr-' in remoteCluster['master']['public_dns']:
        remoteCluster['master']['public_dns'] = remoteHost
        remoteCluster['master']['private_dns'] = remoteHost

    # Sorta hacky but we need to check whether or not a master node is 
    # associated with the cluster being imported before proceeding
    _instances = yield waitForInstances([remoteCluster], 
                                        [updateTask(taskName,
                                                    'Waiting for populated master node'),
                                         waitForPopulatedMasterNode(srcCluster,
                                                                    authToken,
                                                                    WAIT_FOR_STATE_TRIES)])
                                                                    
    if not _instances.succeeded:
        raise Error('Could not retrieve master node from imported cluster.')

    baseConf = config.configFromMap(cluster.config.conf)
    remoteClusterConf = config.configFromMap({'general.src_cluster': srcCluster},
                                             base=baseConf)
    cl = cluster.update(config=remoteClusterConf)

    cl = cl.setMaster(remoteCluster.get('master')) 
    yield state.persistManager.saveCluster(cl)

    log.msg('DEBUG importCluster: About to run tests on master node')

    _instances = yield waitForInstances([remoteCluster.get('master')],
                                       [updateTask(taskName,
                                                   'Waiting for master'),
                                        waitForState(credClient,
                                                     'running',
                                                     WAIT_FOR_STATE_TRIES),
                                        _saveCluster,
                                        waitForSSH(cluster.config('ssh.user'),
                                                   cluster.config('ssh.options'),
                                                   WAIT_FOR_SSH_TRIES),
                                        _saveCluster,
                                        updateTask(taskName,
                                                   'SSH up'),
                                        updateTask(taskName,
                                                   'Master in running state')])

    if not _instances.succeeded:
        raise Error('Failed to import cluster')

    # TODO: Maybe implement another set of checks here on our exec nodes.
    if remoteCluster.get('exec_nodes'):
        cl = cl.addExecNodes(remoteCluster.get('exec_nodes'))
        yield state.persistManager.saveCluster(cl)

    cl = yield state.persistManager.loadCluster(cl.clusterName,
                                                cl.userName)
    cl = cl.setState(cl.RUNNING)
    yield state.persistManager.saveCluster(cl)
    
    defer.returnValue(cl)

def updateTask(taskName, msg):
    @defer.inlineCallbacks
    def _updateTask(instances):
        def _addMsg(t):
            tt = t.addMessage(task.MSG_SILENT,
                              msg)
            tt = tt.addMessage(task.MSG_SILENT,
                               'Instances: %d' % len(instances))
            tt = tt.progress()
            return tt
        
        yield tasks_tx.updateTask(taskName,
                                  _addMsg)
        defer.returnValue(func.Record(succeeded=instances,
                                      failed=[]))

    return _updateTask

def wrapEnsureInstances(f, retries):
    def _wrapEnsureInstances(instances):
        return ensureInstances(f, instances, retries)

    return _wrapEnsureInstances
    
def waitForState(credClient, state, retries):
    @defer.inlineCallbacks
    def _waitForState(instance):
        currInstances = yield credClient.updateInstances([instance])
        currInstance = currInstances[0]
        if currInstance['state'] not in ['pending', state]:
            defer.returnValue(FAILED_INSTANCE)
        else:
            defer.returnValue(currInstance['state'] == state)

    return wrapEnsureInstances(_waitForState, retries)

def waitForSSH(sshUser, sshOptions, retries):
    @defer.inlineCallbacks
    def _waitForSSH(instance):
        try:
            yield ssh.runProcessSSH(instance['public_dns'],
                                    'echo hello',
                                    None,
                                    None,
                                    sshUser,
                                    sshOptions)
        except:
            defer.returnValue(False)

        defer.returnValue(True)            

    return wrapEnsureInstances(_waitForSSH, retries)

def waitForBoot(fileName, sshUser, sshOptions, retries):
    @defer.inlineCallbacks
    def _waitForBoot(instance):
        try:
            yield ssh.runProcessSSH(instance['public_dns'],
                                    'test -e %s' % fileName,
                                    None,
                                    None,
                                    sshUser,
                                    sshOptions)
        except:
            ## Should differentiate between SSH failing and file not
            ## existings so we can return FAILED_INSTANCE appropriately
            defer.returnValue(False)

        defer.returnValue(True)
        
    return wrapEnsureInstances(_waitForBoot, retries)


def waitForClusterInfo(cluster, userName, retries):
    @defer.inlineCallbacks
    def _waitForClusterInfo(instance):
        try:
            yield clusters_client_www.listClusters(instance['public_dns'],
                                                   {},
                                                   userName)
        except:
            defer.returnValue(False)

        defer.returnValue(True)

    return wrapEnsureInstances(_waitForClusterInfo, retries)

def waitForPopulatedMasterNode(srcCluster, authToken, retries):
    """Verifies whether or not the master node attribute has been 
    populated for a imported cluster. This attribute is required to proceed
    with a successful import.

    """
    @defer.inlineCallbacks
    def _waitForPopulatedMasterNode(instance):
        retVal = False

        try:
            if instance.get('master'):
                retVal = True
            else:
                cluster = yield clusters_client_www.listClusters(instance.get('public_dns'),
                                                                 {'cluster_name': srcCluster},
                                                                 instance.get('user_name'),
                                                                 authToken)
               
                retVal = cluster.get('master') != None
        except:
            defer.returnValue(retVal)

        defer.returnValue(retVal)

    return wrapEnsureInstances(_waitForPopulatedMasterNode, retries)

@defer.inlineCallbacks
def waitForInstances(instances, workflow):
    """
    Takes instances and a workflow.

    The input to the workflow is the current alive instances
    and the output is alive and dead instances.  Output
    of entire function is alive and dead instances.

    No instances are terminated in this.
    """
    retInstances = func.Record(succeeded=instances,
                               failed=[])

    failedInstances = []
    
    for f in workflow:
        retInstances = yield f(retInstances.succeeded)
        failedInstances.extend(retInstances.failed)

        ## If there aren't any instances left to check
        ## no reason to keep doing work.
        if not retInstances.succeeded:
            break


    defer.returnValue(func.Record(succeeded=retInstances.succeeded,
                                  failed=failedInstances))
    
@defer.inlineCallbacks
def runInstances(credClient,
                 ami,
                 key,
                 iType,
                 groups,
                 availZone,
                 bidPrice,
                 minInstances,
                 maxInstances,
                 userData):
    def _runInstances(num):
        if bidPrice:
            return credClient.runSpotInstances(bidPrice=bidPrice,
                                               ami=ami,
                                               key=key,
                                               instanceType=iType,
                                               groups=groups,
                                               availabilityZone=availZone,
                                               numInstances=num,
                                               userData=userData)
        else:
            return credClient.runInstances(ami=ami,
                                           key=key,
                                           instanceType=iType,
                                           groups=groups,
                                           availabilityZone=availZone,
                                           numInstances=num,
                                           userData=userData)

    instances = []
    @defer.inlineCallbacks
    def _startInstances():
        startedInstances = yield _runInstances(maxInstances - len(instances))
        instances.extend(startedInstances)
        if len(instances) < minInstances:
            raise InstanceStartError('Wanted %d instances got %d' %
                                     (maxInstances - len(instances),
                                      len(startedInstances)))


    try:
        yield defer_utils.tryUntil(RUN_INSTANCE_TRIES,
                                   _startInstances,
                                   onFailure=defer_utils.sleep(30))
    except Exception, err:
        ## If we got an exception then terminate any instances
        ## that were started and reraise exception.
        ## The last thing we want is to leak instances
        ##
        ## This is not completely safe!  We should probably
        ## raise an exception with the started instances in it
        ## and let the caller decide what to do with them
        log.err('Error starting instances')
        log.err(err)
        defer_utils.mapSerial(lambda iChunk :
                                  credClient.terminateInstances(iChunk),
                              func.chunk(5, instances))

    defer.returnValue(instances)
        

@defer.inlineCallbacks
def ensureInstances(f, instances, retries):
    """
    Applies function f to each instance in instances.  f
    is a deferred that can evaluate to True, False, or
    FAILED_INSTANCE

    Returns a record with .succeeded and .failed
    """

    retryInstances = []
    
    succeeded = []
    failed = []
    while retries > 0 and instances:
        yield defer_utils.sleep(30)()
        for i in instances:
            ret = yield f(i)
            if ret == FAILED_INSTANCE:
                failed.append(i)
            elif ret:
                succeeded.append(i)
            else:
                retryInstances.append(i)

        retries -= 1
        instances = retryInstances
        retryInstances = []

    if instances:
        failed.extend(instances)

    defer.returnValue(func.Record(succeeded=succeeded,
                                  failed=failed))


#
# The cluster manager controls every aspect of clusters including starting
# stoping viewing information and adding instances.  There is an interface
# for both web-facing aspects and internal
#
import os
import json

from twisted.internet import defer
from twisted.internet import reactor

from twisted.python import log

from igs.utils import config
from igs.utils import core
from igs.utils import functional as func

from igs_tx.utils import global_state
from igs_tx.utils import ssh

from vappio.tasks import task

from vappio.instance import config as vappio_config

from vappio_tx.utils import queue
from vappio_tx.utils import core as vappio_tx_core

from vappio_tx.mq import client

from vappio_tx.clusters import persist

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.internal_client import credentials as cred_client

from vappio_tx.www_client import clusters as clusters_client_www

RUN_INSTANCE_TRIES = 4

WAIT_FOR_STATE_TRIES = 50

WAIT_FOR_SSH_TRIES = WAIT_FOR_STATE_TRIES

WAIT_FOR_BOOT_TRIES = WAIT_FOR_STATE_TRIES

INSTANCE_REFRESH_RATE = 30

REMOVE_TERMINATED_CLUSTER_TIMEOUT = 120

CLUSTER_REFRESH_FREQUENCY = 60

class State:
    """
    Maintain state information.  This should always be in a state in which
    it can be repopulated in case of a crash
    """

    def __init__(self, conf):
        self.conf = conf
        self.clustersCache = {}
    

def loadRemoteClusterData(cl, mq, state):
    # If there is a master, contact it to get updated exec and datanodes
    # Set the timeout very short (5 seconds) so we can respond to the
    # webserver in time and reduce the number of retries to 3
    #
    # If there is no master, simply respond with the cluster we have
    if cl.clusterName != 'local' and cl.master and cl.state == cl.RUNNING:
        clusterLoadDefer = clusters_client_www.loadCluster(cl.master['public_dns'],
                                                           'local',
                                                           None,
                                                           timeout=10,
                                                           tries=3)
        clusterLoadDefer.addCallback(lambda cluster : cl.update(execNodes=cluster['exec_nodes']
                                                                ).update(dataNodes=cluster['data_nodes']))
        clusterLoadDefer.addErrback(lambda _fail : cl.setState(cl.UNRESPONSIVE))
        
        return clusterLoadDefer
    else:
        credClient = cred_client.CredentialClient(cl.credName,
                                                  mq,
                                                  state.conf)
        nodeUpdates = []
        if cl.execNodes:
            nodeUpdates.append(credClient.updateInstances(cl.execNodes))
        else:
            nodeUpdates.append(defer.succeed([]))

        if cl.dataNodes:
            nodeUpdates.append(credClient.updateInstances(cl.dataNodes))
        else:
            nodeUpdates.append(defer.succeed([]))

        updateDefer = defer.DeferredList(nodeUpdates)
        updateDefer.addCallback(lambda r : cl.update(execNodes=r[0][1]).update(dataNodes=r[1][1]))
            
        return updateDefer
        

def saveCluster(cl, state=None):
    if state:
        state.clustersCache[(cl.clusterName, cl.userName)] = cl
    saved = persist.saveCluster(cl)
    saved.addCallback(lambda _ : cl)
    return saved

#
# These callbacks handle things associated with tasks
def handleTaskStartCluster(state, mq, request):
    d = tasks_tx.updateTask(request['task_name'],
                            lambda t : t.setState(task.TASK_RUNNING))
    
    cl = persist.Cluster(request['cluster'],
                         request['user_name'],
                         request['cred_name'],
                         config.configFromMap({}))
    d.addCallback(lambda _ : startMaster(state, mq, request['task_name'], cl))

    def _completeTask(cl):
        updateTaskDefer = tasks_tx.updateTask(request['task_name'],
                                              lambda t : t.setState(task.TASK_COMPLETED).progress())
        updateTaskDefer.addCallback(lambda _ : cl)
        return updateTaskDefer

    d.addCallback(_completeTask)

    def _removeClusterOnFailure(f):
        """
        When a failure occurs, set the cluster to failed then set it up a timer to
        remove it
        """
        def _removeCluster():
            innerLoadClusterDefer = persist.loadCluster(cl.clusterName, cl.userName)
            
            def _reallyRemoveCluster(cl):
                if cl.state == cl.FAILED:
                    return persist.removeCluster(cl)

            innerLoadClusterDefer.addCallback(_reallyRemoveCluster)
            innerLoadClusterDefer.addErrback(log.err)

        loadClusterDefer = persist.loadCluster(cl.clusterName, cl.userName)
        loadClusterDefer.addCallback(lambda cl : saveCluster(cl.setState(cl.FAILED), state))
        loadClusterDefer.addCallback(lambda cl : reactor.callLater(REMOVE_TERMINATED_CLUSTER_TIMEOUT,
                                                                   _removeCluster))
        loadClusterDefer.addCallback(lambda _ : f)

        return loadClusterDefer

    d.addErrback(_removeClusterOnFailure)
    
    return d
        
    
    
def handleTaskTerminateCluster(state, mq, request):
    def _terminateCluster(cl):
        credClient = cred_client.CredentialClient(cl.credName,
                                                  mq,
                                                  state.conf)

        #
        # Terminate 5 at a time
        terminateDefer = deferredMap(lambda instances : credClient.terminateInstances(instances),
                                     list(func.chunk(5, cl.execNodes + cl.dataNodes)))



        #
        # Now terminate the master
        def _terminateMasterIfPresent(_):
            if cl.master:
                return credClient.terminateInstances([cl.master])
            else:
                return defer.succeed(None)
            
        terminateDefer.addCallback(_terminateMasterIfPresent)

        def _logErr(f):
            log.err(f)
            return f

        terminateDefer.addErrback(_logErr)
        return terminateDefer

    # Start task running
    d = tasks_tx.updateTask(request['task_name'],
                            lambda t : t.setState(task.TASK_RUNNING))
    if request['cluster'] != 'local':
        # If we are terminated a remote cluster
        def _terminate(cl):
            terminateDefer = defer.succeed(True)
            terminateDefer.addCallback(lambda _ : clusters_client_www.terminateCluster(cl.master['public_dns'],
                                                                                       'local',
                                                                                       None))

            def _removeCluster(cl):
                #
                # Load the cluster again to make sure it is still in terminated
                loadClusterDefer = persist.loadCluster(cl.clusterName, cl.userName)
                def _removeForReal(cl):
                    if cl.state == cl.TERMINATED:
                        return persist.removeCluster(cl)

                loadClusterDefer.addCallback(_removeForReal)
                return loadClusterDefer

            def _terminateFailed(_f):
                return _terminateCluster(cl)
            
            def _setTerminated(_):
                cluster = cl.setState(cl.TERMINATED)
                #
                # Remove the cluster in a few minutes
                reactor.callLater(REMOVE_TERMINATED_CLUSTER_TIMEOUT, _removeCluster, cluster)
                return cluster


            # If our webservice call failed, forcibly terminate
            terminateDefer.addErrback(_terminateFailed)
            terminateDefer.addCallback(_setTerminated)
            terminateDefer.addCallback(saveCluster, state)
            return terminateDefer

        d.addCallback(lambda _ : persist.loadCluster(request['cluster'], request['user_name']))
        d.addCallback(loadRemoteClusterData, mq, state)
        d.addCallback(_terminate)
    else:
        # Now terminating ourselves
        d.addCallback(lambda _ : persist.loadCluster('local', None))
        d.addCallback(lambda cl : cl.setState(cl.TERMINATED))
        d.addCallback(saveCluster, state)
        d.addCallback(_terminateCluster)
                
    def _completeTask(anyThing):
        updateTaskDefer = tasks_tx.updateTask(request['task_name'],
                                              lambda t : t.setState(task.TASK_COMPLETED
                                                                    ).progress())
        updateTaskDefer.addCallback(lambda _ : anyThing)
        return updateTaskDefer

    d.addCallback(_completeTask)
    return d

def handleTaskAddInstances(state, mq, request):
    d = persist.loadCluster('local', None)

    if request['num_exec'] > 0:
        d.addCallback(lambda cl : startExecNodes(state,
                                                 mq,
                                                 request['task_name'],
                                                 request['num_exec'],
                                                 cl))

    def _completeTask(cl):
        updateTaskDefer = tasks_tx.updateTask(request['task_name'],
                                              lambda t : t.setState(task.TASK_COMPLETED).progress())
        updateTaskDefer.addCallback(lambda _ : cl)
        return updateTaskDefer

    d.addCallback(_completeTask)
    return d


def removeDeadClusters():
    d = persist.loadClustersAdmin()

    def _removeDead(cls):
        return deferredMap(persist.removeCluster,
                           [c for c in cls if c.state in [c.FAILED, c.TERMINATED]])

    d.addCallback(_removeDead)

    return d

def refreshClusters(mq, state):
    d = persist.loadClustersAdmin()

    def _getAllClusterInfo(cls):
        # If there isn't anything there, then quickly set the cache
        # to the local version of the clusters because getting all
        # of the data could take awhile and we don't want queries to say
        # no cluster exists when it actually does.  stale data is
        # better than no data
        if not state.clustersCache:
            state.clustersCache = dict([((c.clusterName, c.userName), c)
                                        for c in cls])
        return deferredMap(lambda c : loadRemoteClusterData(c, mq, state), cls)
    
    def _addClustersToCache(cls):
        state.clustersCache = dict([((c.clusterName, c.userName), c)
                                    for c in cls])
        reactor.callLater(CLUSTER_REFRESH_FREQUENCY, refreshClusters, mq, state)


    def _logError(f):
        log.err(f)
        reactor.callLater(CLUSTER_REFRESH_FREQUENCY, refreshClusters, mq, state)
        
    d.addCallback(_getAllClusterInfo)
    d.addCallback(_addClustersToCache)
    d.addErrback(_logError)


#
# These callbacks must return immediatly
def handleWWWClusterInfo(state, mq, request):
    if request['cluster'] == 'local' and ('local', None) in state.clustersCache:
        queue.returnQueueSuccess(mq,
                                 request['return_queue'],
                                 persist.clusterToDict(state.clustersCache[('local', None)]))
    elif (request['cluster'], request['user_name']) in state.clustersCache:
        queue.returnQueueSuccess(mq,
                                 request['return_queue'],
                                 persist.clusterToDict(state.clustersCache[(request['cluster'],
                                                                            request['user_name'])]))
    else:
        queue.returnQueueError(mq, request['return_queue'], 'Cluster not found')

    return defer.succeed(True)

def handleWWWListClusters(state, mq, request):
    d = persist.loadAllClusters(request['user_name'])

    def _convertToDict(cls):
        return [persist.clusterToDict(c) for c in cls]

    d.addCallback(_convertToDict)

    def _sendSuccess(cls):
        queue.returnQueueSuccess(mq, request['return_queue'], cls)

    d.addCallback(_sendSuccess)

    def _sendError(f):
        queue.returnQueueFailure(mq, request['return_queue'], f)
        return f

    d.addErrback(_sendError)
    
    return d


def handleWWWConfigCluster(state, mq, request):
    d = persist.loadCluster(request['cluster'], request['user_name'])

    def _extractConf(c):
        return c.conf

    d.addCallback(_extractConf)
    
    def _confToJson(conf):
        return json.dumps(conf)

    d.addCallback(_confToJson)

    def _returnJson(js):
        queue.returnQueueSuccess(mq, request['return_queue'], js)

    d.addCallback(_returnJson)

    def _sendError(f):
        queue.returnQueueFailure(mq, request['return_queue'], f)
        return f

    d.addErrback(_sendError)

    return d
    

def loadLocalCluster(mq, state):
    """If local cluster is not present, load it"""

    d = persist.loadCluster('local', None)

    def _clusterDoesnotExist(f):
        f.trap(persist.ClusterNotFoundError)

        if os.path.exists('/tmp/cred-info'):
            cert, pkey, ctype, metadata = open('/tmp/cred-info').read().split('\t')
            saveDefer = cred_client.saveCredential('local',
                                                   'Local credential',
                                                   ctype,
                                                   open(cert).read(),
                                                   open(pkey).read(),
                                                   metadata and dict([v.split('=', 1) for v in metadata.split(',')]) or {},
                                                   config.configFromStream(open('/tmp/machine.conf'), lazy=True))
            credClient = cred_client.CredentialClient('local',
                                                      mq,
                                                      state.conf)
            saveDefer.addCallback(lambda _ : credClient.listInstances())
        else:
            saveDefer = cred_client.saveCredential('local',
                                                   'Local credential',
                                                   'local',
                                                   None,
                                                   None,
                                                   {},
                                                   config.configFromMap({}))
            saveDefer.addCallback(lambda _ : [])

        def _addCluster(instances):
            cl = persist.Cluster('local',
                                 None,
                                 'local',
                                 config.configFromMap({'config_loaded': True},
                                                      base=config.configFromStream(open('/tmp/machine.conf'), base=config.configFromEnv())))

            master = func.find(lambda i : i.master['public_dns'] == cl.config('MASTER_IP'),
                               instances)

            if master is None:
                master = dict(instance_id='local',
                              ami_id=None,
                              public_dns=cl.config('MASTER_IP'),
                              private_dns=cl.config('MASTER_IP'),
                              state='running',
                              key=None,
                              index=None,
                              instance_type=None,
                              launch=None,
                              availability_zone=None,
                              monitor=None,
                              spot_request_id=None,
                              bid_price=None)
            
            cl = cl.setMaster(master)
            cl = cl.setState(cl.RUNNING)
            clusterSaveDefer = persist.saveCluster(cl)
            clusterSaveDefer.addCallback(lambda _ : cl)
            return clusterSaveDefer

        saveDefer.addCallback(_addCluster)
        return saveDefer
    
    d.addErrback(_clusterDoesnotExist)
    return d


def startMaster(state, mq, taskName, cl):
    credClient = cred_client.CredentialClient(cl.credName,
                                              mq,
                                              state.conf)
    
    d = tasks_tx.updateTask(taskName,
                            lambda t : t.addMessage(task.MSG_SILENT,
                                                    'Starting master for ' + cl.clusterName))
    d.addCallback(lambda _ : cl)
    d.addCallback(saveCluster, state)

    def _loadConfig(cl):
        loadConfig = credClient.credentialConfig()
        loadConfig.addCallback(lambda c : cl.update(config=config.configFromMap(c)))
        return loadConfig

    d.addCallback(_loadConfig)
    
    def _createDataFilesAndStartMaster(cl):
        mode = [vappio_config.MASTER_NODE]
        masterConf = vappio_config.createDataFile(cl.config,
                                                  mode,
                                                  outFile='/tmp/machine.' + global_state.make_ref() + '.conf')

        dataFile = vappio_config.createMasterDataFile(cl, masterConf)

        masterDefer = runInstancesWithRetry(credClient,
                                            cl.config('cluster.ami'),
                                            cl.config('cluster.key'),
                                            cl.config('cluster.master_type'),
                                            cl.config('cluster.master_groups'),
                                            cl.config('cluster.availability_zone', default=None),
                                            cl.config('cluster.master_bid_price', default=None),
                                            1,
                                            open(dataFile).read())
        masterDefer.addCallback(lambda l : cl.setMaster(l[0]))
        masterDefer.addCallback(saveCluster, state)

        def _removeFiles(cl):
            os.remove(masterConf)
            os.remove(dataFile)
            return cl

        masterDefer.addCallback(_removeFiles)
        
        return masterDefer
        
    
    d.addCallback(_createDataFilesAndStartMaster)

        
    def _masterStartedUpdate(cl):
        updateTask = tasks_tx.updateTask(taskName,
                                         lambda t : t.addMessage(task.MSG_SILENT,
                                                        'Master started'))
        
        updateTask.addCallback(lambda _ : cl)
        return updateTask


    d.addCallback(_masterStartedUpdate)

    def _waitForState(cl):
        stateDefer = retryAndTerminate(credClient,
                                       WAIT_FOR_STATE_TRIES,
                                       [cl.master],
                                       lambda i : i['state'] == 'running')

        def _masterDead(l):
            if not l:
                raise Exception('Master did not come to running state')
            return cl.setMaster(l[0])

        stateDefer.addCallback(_masterDead)
        stateDefer.addCallback(saveCluster, state)
        return stateDefer

    d.addCallback(_waitForState)
    
    def _waitForSSH(cl):
        sshDefer = retryAndTerminateDeferred(credClient,
                                             WAIT_FOR_SSH_TRIES,
                                             [cl.master],
                                             lambda i : ssh.runProcessSSH(i['public_dns'],
                                                                          'echo hello',
                                                                          None,
                                                                          None,
                                                                          cl.config('ssh.user'),
                                                                          cl.config('ssh.options')
                                                                          ).addCallback(lambda _ : True).addErrback(lambda _ : False))

        def _masterDead(l):
            if not l:
                raise Exception('Master did not respond to SSH')

            return cl.setMaster(l[0])

        sshDefer.addCallback(_masterDead)
        sshDefer.addCallback(saveCluster, state)
        return sshDefer

    d.addCallback(_waitForSSH)
    
    def _waitForRemoteBoot(cl):
        bootDefer = retryAndTerminateDeferred(credClient,
                                              WAIT_FOR_BOOT_TRIES,
                                              [cl.master],
                                              lambda i : ssh.runProcessSSH(i['public_dns'],
                                                                           'test -e /tmp/startup_complete',
                                                                           None,
                                                                           None,
                                                                           cl.config('ssh.user'),
                                                                           cl.config('ssh.options')
                                                                           ).addCallback(lambda _ : True).addErrback(lambda _ : False))
        def _masterDead(l):
            if not l:
                raise Exception('Master did not boot up')

            return cl.setMaster(l[0]).setState(cl.RUNNING)

        bootDefer.addCallback(_masterDead)
        bootDefer.addCallback(saveCluster, state)
        return bootDefer

    d.addCallback(_waitForRemoteBoot)
        
    return d


def startExecNodes(state, mq, taskName, numExec, cl):
    credClient = cred_client.CredentialClient(cl.credName,
                                              mq,
                                              state.conf)
    d = tasks_tx.updateTask(taskName,
                            lambda t : t.addMessage(task.MSG_SILENT,
                                                    'Adding %d instances to %s ' % (numExec, cl.clusterName)))

    def _createDataFilesAndStartExec(_):
        dataFile = vappio_config.createExecDataFile(cl.config, cl.master, '/tmp/machine.conf')
        execDefer = runInstancesWithRetry(credClient,
                                          cl.config('cluster.ami'),
                                          cl.config('cluster.key'),
                                          cl.config('cluster.exec_type'),
                                          cl.config('cluster.exec_groups'),
                                          cl.config('cluster.availability_zone', default=None),
                                          cl.config('cluster.exec_bid_price', default=None),
                                          numExec,
                                          open(dataFile).read())


        def _addExecNodesAndUpdateTask(l):
            return tasks_tx.updateTask(taskName,
                                       lambda t : t.addMessage(task.MSG_SILENT,
                                                               'Started %d instances' % len(l))
                                       ).addCallback(lambda _ : cl.addExecNodes(l))

        execDefer.addCallback(_addExecNodesAndUpdateTask)
        execDefer.addCallback(saveCluster, state)
        
        def _removeFiles(cl):
            os.remove(dataFile)
            return cl

        execDefer.addCallback(_removeFiles)
        return execDefer

    d.addCallback(_createDataFilesAndStartExec)

    def _waitForState(cl):
        stateDefer = retryAndTerminate(credClient,
                                       WAIT_FOR_STATE_TRIES,
                                       cl.execNodes,
                                       lambda i : i['state'] == 'running')

        def _updateTaskIfAnyFailed(l):
            cluster = cl.update(execNodes=l)
            
            if len(l) != len(cl.execNodes):
                return tasks_tx.updateTask(taskName,
                                           lambda t : t.addMessage(task.MSG_ERROR,
                                                                   'Not all exec nodes started')
                                           ).addCallback(lambda _ : cluster)
            else:
                return defer.succeed(cluster)
                
        stateDefer.addCallback(_updateTaskIfAnyFailed)
        stateDefer.addCallback(saveCluster, state)
        return stateDefer

    d.addCallback(_waitForState)

    def _waitForSSH(cl):
        sshDefer = retryAndTerminateDeferred(credClient,
                                             WAIT_FOR_SSH_TRIES,
                                             cl.execNodes,
                                             lambda i : ssh.runProcessSSH(i['public_dns'],
                                                                          'echo hello',
                                                                          None,
                                                                          None,
                                                                          cl.config('ssh.user'),
                                                                          cl.config('ssh.options')
                                                                          ).addCallback(lambda _ : True).addErrback(lambda _ : False))


        def _updateTaskIfAnyFailed(l):
            cluster = cl.update(execNodes=l)
            
            if len(l) != len(cl.execNodes):
                return tasks_tx.updateTask(taskName,
                                           lambda t : t.addMessage(task.MSG_ERROR,
                                                                   'Not all exec nodes responded to SSH')
                                           ).addCallback(lambda _ : cluster)
            else:
                return defer.succeed(cluster)
                
        sshDefer.addCallback(_updateTaskIfAnyFailed)
        sshDefer.addCallback(saveCluster, state)
        return sshDefer

    d.addCallback(_waitForSSH)
    
    def _waitForRemoteBoot(cl):
        bootDefer = retryAndTerminateDeferred(credClient,
                                              WAIT_FOR_BOOT_TRIES,
                                              cl.execNodes,
                                              lambda i : ssh.runProcessSSH(i['public_dns'],
                                                                           'test -e /tmp/startup_complete',
                                                                           None,
                                                                           None,
                                                                           cl.config('ssh.user'),
                                                                           cl.config('ssh.options')
                                                                           ).addCallback(lambda _ : True).addErrback(lambda _ : False))

        def _updateTaskIfAnyFailed(l):
            cluster = cl.update(execNodes=l)
            
            if len(l) != len(cl.execNodes):
                return tasks_tx.updateTask(taskName,
                                           lambda t : t.addMessage(task.MSG_ERROR,
                                                                   'Not all machines booted')
                                           ).addCallback(lambda _ : cluster)
            else:
                return defer.succeed(cluster)
                
        bootDefer.addCallback(_updateTaskIfAnyFailed)
        bootDefer.addCallback(saveCluster, state)
        return bootDefer

    d.addCallback(_waitForRemoteBoot)
        
    return d


    
def runInstancesWithRetry(credClient,
                          ami,
                          key,
                          iType,
                          groups,
                          availZone,
                          bidPrice,
                          numInstances,
                          userData):


    d = defer.Deferred()
    groups = [g.strip() for g in groups.split(',')]
    
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
    def _runAndRetry(retries):
        if retries > 0:
            num = numInstances - len(instances)
            runDefer = _runInstances(num)
            runDefer.addCallback(lambda i : instances.extend(i))
            runDefer.addErrback(d.errback)

            def _retry(_):
                if numInstances != len(instances):
                    r = retries - 1
                    _runAndRetry(r)
                else:
                    d.callback(instances)
            runDefer.addCallback(_retry)
        else:
            d.callback(instances)
                
    _runAndRetry(RUN_INSTANCE_TRIES)
    return d


def retryAndTerminate(credClient, retries, instances, f):
    """
    f does not return a deferred in this case
    
    f is called on every instance in instances.  If any calls
    return False, the instance list is updated after INSTANCE_REFRESH_RATE
    seconds have passed and repeated.  If 'retries' attempts have been done and
    failed, all those instances which returned False are terminated.
    """

    d = defer.Deferred()

    #
    # If they already pass, return them
    if all((f(i) for i in instances)):
        d.callback(instances)
        return d

    
    def _retry(retries):
        if retries > 0:
            updateDefer = credClient.updateInstances(instances)

            def _retryIfNecessary(instances):
                if all((f(i) for i in instances)):
                    d.callback(instances)
                else:
                    reactor.callLater(INSTANCE_REFRESH_RATE, _retry, retries - 1)

            updateDefer.addCallback(_retryIfNecessary)
            updateDefer.addErrback(d.errback)
        else:
            badInstances = [i for i in instances if not f(i)]
            goodInstances = [i for i in instances if f(i)]

            terminateDefer = credClient.terminateInstances(badInstances)
            terminateDefer.addCallback(lambda _ : d.callback(goodInstances))
            terminateDefer.addErrback(d.errback)

    reactor.callLater(INSTANCE_REFRESH_RATE, _retry, retries)
    return d

def deferredMap(f, l):
    d = defer.Deferred()

    res = []
    
    def _deferredMap(idx):
        if idx < len(l):
            fDefer = f(l[idx])
            
            def _success(r):
                res.append(r)
                _deferredMap(idx + 1)

            fDefer.addCallback(_success)
            fDefer.addErrback(d.errback)
        else:
            d.callback(res)

    _deferredMap(0)
    return d


def retryAndTerminateDeferred(credClient, retries, instances, f):
    """
    f does return a deferred.
    
    f is called on every instance in instances.  If any calls
    return False, the instance list is updated after INSTANCE_REFRESH_RATE
    seconds have passed and repeated.  If 'retries' attempts have been done and
    failed, all those instances which returned False are terminated.
    """

    d = defer.Deferred()

    
    def _retry(retries):
        if retries > 0:
            updateDefer = credClient.updateInstances(instances)

            def _retryIfNecessary(instances):
                checkInstancesDefer = deferredMap(f, instances)

                def _checkRes(res):
                    if all((b for b in res)):
                        d.callback(instances)
                    else:
                        reactor.callLater(INSTANCE_REFRESH_RATE, _retry, retries - 1)

                checkInstancesDefer.addCallback(_checkRes)
                return checkInstancesDefer

            updateDefer.addCallback(_retryIfNecessary)
            updateDefer.addErrback(d.errback)
        else:
            badInstances = [i for i in instances if not f(i)]
            goodInstances = [i for i in instances if f(i)]

            terminateDefer = credClient.terminateInstances(badInstances)
            terminateDefer.addCallback(lambda _ : d.callback(goodInstances))
            terminateDefer.addErrback(d.errback)

    reactor.callLater(0, _retry, retries)
    return d


#
# Just a shorthand definition
queueSubscription = vappio_tx_core.QueueSubscription

def makeService(conf):
    mqService = client.makeService(conf)

    mqFactory = mqService.mqFactory

    # State is currently not used, but kept around for future purposes
    state = State(conf)

    # Startup list
    startUpDefer = loadLocalCluster(mqFactory, state)
    startUpDefer.addCallback(lambda _ : removeDeadClusters())
    startUpDefer.addCallback(lambda _ : refreshClusters(mqFactory, state))
    

    #
    # Now add web frontend queues
    successF = lambda f : lambda mq, body : f(state, mq, body)
    failTaskF = lambda mq, body, f : 'task_name' in body and tasks_tx.updateTask(body['task_name'],
                                                                                 lambda t : t.setState(task.TASK_FAILED
                                                                                                       ).addFailure(f))
    returnQueueF = lambda mq, body, f : queue.returnQueueFailure(mq, body['return_queue'], f)
    
    #
    # These require a task
    queue.ensureRequestAndSubscribeTask(mqFactory,
                                        queueSubscription(ensureF=core.keysInDictCurry(['cluster',
                                                                                        'num_exec',
                                                                                        'num_data',
                                                                                        'cred_name']),
                                                          successF=successF(handleTaskStartCluster),
                                                          failureF=failTaskF),
                                        'startCluster',
                                        conf('clusters.startcluster_www'),
                                        conf('clusters.startcluster_queue'),
                                        conf('clusters.concurrent_startcluster'))
    

    queue.ensureRequestAndSubscribeTask(mqFactory,
                                        queueSubscription(ensureF=core.keysInDictCurry(['cluster']),
                                                          successF=successF(handleTaskTerminateCluster),
                                                          failureF=failTaskF),
                                        'terminateCluster',
                                        conf('clusters.terminatecluster_www'),
                                        conf('clusters.terminatecluster_queue'),
                                        conf('clusters.concurrent_terminatecluster'))


    queue.ensureRequestAndSubscribeForwardTask(mqFactory,
                                               queueSubscription(ensureF=core.keysInDictCurry(['cluster',
                                                                                               'num_exec',
                                                                                               'num_data']),
                                                                 successF=successF(handleTaskAddInstances),
                                                                 failureF=failTaskF),
                                               'addInstances',
                                               conf('www.url_prefix') + '/' + os.path.basename(conf('clusters.addinstances_www')),                                               
                                               conf('clusters.addinstances_www'),
                                               conf('clusters.addinstances_queue'),
                                               conf('clusters.concurrent_addinstances'))
    

    #
    # These return immediatly
    queue.ensureRequestAndSubscribe(mqFactory,
                                    queueSubscription(ensureF=core.keysInDictCurry(['cluster']),
                                                      successF=successF(handleWWWClusterInfo),
                                                      failureF=returnQueueF),
                                    conf('clusters.clusterinfo_www'),
                                    conf('clusters.concurrent_clusterinfo'))

    
    queue.ensureRequestAndSubscribe(mqFactory,
                                    queueSubscription(ensureF=None,
                                                      successF=successF(handleWWWListClusters),
                                                      failureF=returnQueueF),
                                    conf('clusters.listclusters_www'),
                                    conf('clusters.concurrent_listclusters'))

    queue.ensureRequestAndSubscribe(mqFactory,
                                    queueSubscription(ensureF=core.keysInDictCurry(['cluster']),
                                                      successF=successF(handleWWWConfigCluster),
                                                      failureF=returnQueueF),
                                    conf('clusters.configcluster_www'),
                                    conf('clusters.concurrent_configcluster'))
    
        
    return mqService

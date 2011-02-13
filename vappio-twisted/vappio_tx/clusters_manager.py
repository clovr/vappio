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

from igs_tx.utils import defer_utils
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

    d.addCallback(lambda _ : persist.loadCluster(request['cluster'], request['user_name']))

    def _continueIfTerminated(cl):
        if cl.state in [cl.TERMINATED, cl.FAILED]:
            raise persist.ClusterNotFoundError(cl.clusterName)

    d.addCallback(_continueIfTerminated)
    
    def _createCluster(f):
        f.trap(persist.ClusterNotFoundError)
        cl = persist.Cluster(request['cluster'],
                             request['user_name'],
                             request['cred_name'],
                             config.configFromMap({}))
        startMasterDefer = startMaster(state, mq, request['task_name'], cl)
        if request['num_exec'] > 0 or request['num_data'] > 0:
            def _addInstances(cl):
                log.msg('Started master successfully, trying to start any exec nodes')
                addInstancesDefer = clusters_client_www.addInstances('localhost',
                                                                     request['cluster'],
                                                                     request['user_name'],
                                                                     request['num_exec'],
                                                                     request['num_data'])

                def _loadLocalTask(taskName):
                    loadTaskDefer = tasks_tx.loadTask(request['task_name'])
                    loadTaskDefer.addCallback(lambda t : tasks_tx.blockOnTaskAndForward('localhost',
                                                                                        request['cluster'],
                                                                                        taskName,
                                                                                        t))
                    return loadTaskDefer
                
                addInstancesDefer.addCallback(_loadLocalTask)
                addInstancesDefer.addCallback(lambda _ : cl)
                return addInstancesDefer

            startMasterDefer.addCallback(_addInstances)
        return startMasterDefer

    d.addErrback(_createCluster)

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
        def _removeCluster(cl):
            innerLoadClusterDefer = persist.loadCluster(cl.clusterName, cl.userName)
            
            def _reallyRemoveCluster(cl):
                if cl.state == cl.FAILED:
                    return persist.removeCluster(cl)

            innerLoadClusterDefer.addCallback(_reallyRemoveCluster)
            innerLoadClusterDefer.addErrback(log.err)

        loadClusterDefer = persist.loadCluster(request['cluster'], request['user_name'])
        loadClusterDefer.addCallback(lambda cl : saveCluster(cl.setState(cl.FAILED), state))
        loadClusterDefer.addCallback(lambda cl : reactor.callLater(REMOVE_TERMINATED_CLUSTER_TIMEOUT,
                                                                   _removeCluster,
                                                                   cl))
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
        terminateDefer = defer_utils.mapSerial(lambda instances : credClient.terminateInstances(instances),
                                               func.chunk(5, cl.execNodes + cl.dataNodes))



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
            terminateDefer = clusters_client_www.terminateCluster(cl.master['public_dns'],
                                                                  'local',
                                                                  None)
            terminateDefer.addCallback(lambda taskName :
                                       tasks_tx.loadTask(request['task_name']
                                                         ).addCallback(lambda t :
                                                                       tasks_tx.blockOnTaskAndForward('localhost',
                                                                                                      request['cluster_name'],
                                                                                                      taskName,
                                                                                                      t)))
            
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

def handleTaskTerminateInstances(state, mq, request):
    def _terminateInstancesByCriteria(cl, byCriteria, criteriaValues):
        credClient = cred_client.CredentialClient(cl.credName,
                                                  mq,
                                                  state.conf)
        
        instances = [i for i in cl.execNodes + cl.dataNodes if i[byCriteria] in criteriaValues]
        terminateDefer = defer_utils.mapSerial(credClient.terminateInstances,
                                               func.chunk(5, instances))

        def _logErr(f):
            log.err(f)
            return f

        terminateDefer.addErrback(_logErr)
        
        return terminateDefer
    
    # Start task running
    d = tasks_tx.updateTask(request['task_name'],
                            lambda t : t.setState(task.TASK_RUNNING))

    
    if request['cluster'] != 'local':
        d.addCallback(lambda _ : persist.loadCluster(request['cluster'], request['user_name']))
                
        def _terminateInstances(cl):
            terminateDefer = clusters_client_www.terminateInstances(cl.master['public_dns'],
                                                                    'local',
                                                                    request['user_name'],
                                                                    request['by_criteria'],
                                                                    request['criteria_values'])

            terminateDefer.addCallback(lambda taskName :
                                       tasks_tx.loadTask(request['task_name']
                                                         ).addCallback(lambda t :
                                                                       tasks_tx.blockOnTaskAndForward('localhost',
                                                                                                      request['cluster_name'],
                                                                                                      taskName,
                                                                                                      t)))
            
            def _terminateFailed(f):
                log.err('Termination failed')
                return _terminateInstancesByCriteria(cl, request['by_criteria'], request['criteria_values'])

            terminateDefer.addErrback(_terminateFailed)
            return terminateDefer

        d.addCallback(_terminateInstances)
    else:
        d.addCallback(lambda _ : persist.loadCluster(request['cluster'], request['user_name']))
        d.addCallback(lambda cl : _terminateInstancesByCriteria(cl,
                                                                request['by_criteria'],
                                                                request['criteria_values']))

    def _completeTask(anyThing):
        updateTaskDefer = tasks_tx.updateTask(request['task_name'],
                                              lambda t : t.setState(task.TASK_COMPLETED
                                                                    ).progress())
        updateTaskDefer.addCallback(lambda _ : anyThing)
        return updateTaskDefer

    d.addCallback(_completeTask)
    return d
        
def handleTaskAddInstances(state, mq, request):
    d = tasks_tx.updateTask(request['task_name'],
                            lambda t : t.setState(task.TASK_RUNNING))
    
    d.addCallback(lambda _ : persist.loadCluster('local', None))

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
        return defer_utils.mapSerial(persist.removeCluster,
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
        return defer_utils.mapSerial(lambda c : loadRemoteClusterData(c, mq, state), cls)
    
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

            # Because it takes some amount of time to load the credential, we want
            # to keep on calling listInstances until a non-empty list is returned
            # so we can get the id of ourself.
            def _listInstances():
                liDefer = credClient.listInstances()

                def _failIfEmpty(instances):
                    if not instances:
                        raise Exception('Instance list empty')
                    else:
                        return instances

                liDefer.addCallback(_failIfEmpty)
                return liDefer
            
            saveDefer.addCallback(lambda _ : defer_utils.tryUntil(10, _listInstances, onFailure=defer_utils.sleep(10)))
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

            masterIdx = func.find(lambda i : i['public_dns'] == cl.config('MASTER_IP'),
                                  instances)

            if masterIdx is not None:
                master = instances[masterIdx]
            else:
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

        

    groups = [g.strip() for g in groups.split(',')]

    # Since defer_utils.tryUntil is stateless, we want to encode
    # some state for our function to use
    retryState = dict(desired_instances=numInstances,
                      instances=[])


    def _startInstances(retryState):
        runDefer = _runInstances(retryState['desired_instances'])

        def _onFailure(f):
            retryState['desired_instances'] -= 1
            return f

        runDefer.addErrback(_onFailure)
        runDefer.addCallback(lambda i : retryState['instances'].extend(i))

        def _ensureAllInstances(_):
            if len(retryState['instances']) < retryState['desired_instances']:
                retryState['desired_instances'] = retryState['desired_instances'] - len(retryState['instances'])
                raise Exception('Not all instances started')

        runDefer.addCallback(_ensureAllInstances)
        
        runDefer.addCallback(lambda _ : retryState['instances'])


        return runDefer
    
    runAndRetry = defer_utils.tryUntil(RUN_INSTANCE_TRIES,
                                       lambda : _startInstances(retryState),
                                       onFailure=defer_utils.sleep(30))


    def _failIfNoneStarted(f):
        if not len(retryState['instances']):
            return f
        else:
            return retryState['instances']

    runAndRetry.addErrback(_failIfNoneStarted)
    return runAndRetry

def retryAndTerminateDeferred(credClient, retries, instances, f):
    """
    f does return a deferred.
    
    f is called on every instance in instances.  If any calls
    return False, the instance list is updated after INSTANCE_REFRESH_RATE
    seconds have passed and repeated.  If 'retries' attempts have been done and
    failed, all those instances which returned False are terminated.
    """
    def tryF():
        updateDefer = credClient.updateInstances(instances)
        updateDefer.addCallback(lambda instances : defer_utils.mapSerial(f, instances))

        def _failIfNotAnyFailed(res):
            #
            # If all calls to f succeeded then simply return an updated list of instances
            # otherwise sleep for awhile and return failure and surrounding code will rerun or fail out
            if all(res):
                return credClient.updateInstances(instances)
            else:
                raise Exception('Not all instances succeded')

        updateDefer.addCallback(_failIfNotAnyFailed)

        return updateDefer
        
    retryDefer = defer_utils.tryUntil(retries, tryF, onFailure=defer_utils.sleep(30))

    def _terminateBad(fail):
        log.err(fail)
        
        updateDefer = credClient.updateInstances(instances)
        updateDefer.addCallback(lambda instances : defer_utils.mapSerial(f, instances).addCallback(lambda r : zip(instances, r)))
        
        def _partition(resInstances):
            log.msg(resInstances)
            badInstances = [i for i, r in resInstances if not r]
            goodInstances = [i for i, r in resInstances if r]
            
            terminateDefer = credClient.terminateInstances(badInstances)
            terminateDefer.addCallback(lambda _ : goodInstances)
            return terminateDefer

        updateDefer.addCallback(_partition)
        return updateDefer

    retryDefer.addErrback(_terminateBad)
    
    return retryDefer

def retryAndTerminate(credClient, retries, instances, f):
    return retryAndTerminateDeferred(credClient, retries, instances, lambda i : defer.succeed(f(i)))

#
# Just a shorthand definition
queueSubscription = vappio_tx_core.QueueSubscription


def subscribeToQueues(conf, mqFactory, state):
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


    queue.ensureRequestAndSubscribeTask(mqFactory,
                                        queueSubscription(ensureF=core.keysInDictCurry(['cluster',
                                                                                        'by_criteria',
                                                                                        'criteria_values']),
                                                          successF=successF(handleTaskTerminateInstances),
                                                          failureF=failTaskF),
                                        'terminateInstances',
                                        conf('clusters.terminateinstances_www'),
                                        conf('clusters.terminateinstances_queue'),
                                        conf('clusters.concurrent_terminateinstances'))

    
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
    
        

def makeService(conf):
    mqService = client.makeService(conf)

    mqFactory = mqService.mqFactory

    # State is currently not used, but kept around for future purposes
    state = State(conf)

    # Startup list
    startUpDefer = loadLocalCluster(mqFactory, state)
    startUpDefer.addCallback(lambda _ : removeDeadClusters())
    startUpDefer.addCallback(lambda _ : refreshClusters(mqFactory, state))
    startUpDefer.addCallback(lambda _ : subscribeToQueues(conf, mqFactory, state))

    return mqService

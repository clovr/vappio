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
from igs.utils import functional as func

from igs_tx.utils import defer_utils
from igs_tx.utils import defer_pipe
from igs_tx.utils import errors

from vappio.tasks import task

from vappio_tx.utils import queue

from vappio_tx.mq import client

from vappio_tx.clusters import persist

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.internal_client import credentials as cred_client

from vappio_tx.www_client import clusters as clusters_client_www

from vappio_tx.clusters import start
from vappio_tx.clusters import clusters_cleanup

WAIT_FOR_STATE_TRIES = 50

INSTANCE_REFRESH_RATE = 30

REMOVE_CLUSTER_TIMEOUT = 120

CLUSTER_REFRESH_FREQUENCY = 60

class Error(Exception):
    pass

class State:
    """
    Maintain state information.  This should always be in a state in which
    it can be repopulated in case of a crash
    """

    def __init__(self, conf):
        self.conf = conf
        self.clustersCache = {}
        self.unresponsiveClusters = {}
    
@defer_utils.timeIt
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
        # We want to save the exec and data nodes incase the cluster becomes unresponsive we can
        # terminate it and all it's nodes
        clusterLoadDefer.addCallback(lambda cl : saveCluster(cl, state))
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

@defer_utils.timeIt
@defer.inlineCallbacks
def deleteCluster(credClient, clusterName, userName):
    """
    Removes the cluster from the database.  If any of the instances are still up then
    they are deleted as well.
    """
    try:
        cluster = yield persist.loadCluster(clusterName, userName)


        if cluster.state in [cluster.TERMINATED, cluster.FAILED]:
            yield persist.removeCluster(cluster)

            # Delete any instances that still exist
            instances = cluster.execNodes + cluster.dataNodes
            if cluster.master:
                instances.append(cluster.master)

            instances = yield credClient.updateInstances(instances)
            yield credClient.terminateInstances(instances)
                    
        defer.returnValue(cluster)
    except persist.ClusterNotFoundError:
        # Somebody beat us to deleting it, that's ok
        pass

@defer_utils.timeIt
@defer.inlineCallbacks
def terminateCluster(credClient, clusterName, userName):
    """
    Terminates every instance owned by this cluster and sets the
    cluster to TERMINATED, this does not save it back to the
    databse though.
    """
    cluster = yield persist.loadCluster(clusterName, userName)

    # Terminate 5 at a time
    yield defer_utils.mapSerial(lambda instances : credClient.terminateInstances(instances),
                                func.chunk(5, cluster.execNodes + cluster.dataNodes))

    if cluster.master:
        yield credClient.terminateInstances([cluster.master])

    defer.returnValue(cluster.setState(cluster.TERMINATED))

@defer_utils.timeIt
@defer.inlineCallbacks
def terminateInstancesByCriteria(credClient, clusterName, userName, byCriteria, criteriaValues):
    """
    Terminates instances by the provided criteria, a cluster is returned with these instances
    removed from it
    """
    cluster = yield persist.loadCluster(clusterName, userName)

    # Terminate 5 at a time
    instances = [i
                 for i in cluster.execNodes + cluster.dataNodes
                 if i[byCriteria] in criteriaValues]
    yield defer_utils.mapSerial(credClient.terminateInstances,
                                func.chunk(5, instances))

    execNodes = [i
                 for i in cluster.execNodes
                 if i[byCriteria] not in criteriaValues]
    dataNodes = [i
                 for i in cluster.dataNodes
                 if i[byCriteria] not in criteriaValues]        
    defer.returnValue(cluster.update(execNodes=execNodes, dataNodes=dataNodes))

#
# These callbacks handle things associated with tasks
@defer_utils.timeIt
@defer.inlineCallbacks
def handleTaskStartCluster(request):
    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.setState(task.TASK_RUNNING))

    cluster = persist.Cluster(request.body['cluster'],
                              request.body['user_name'],
                              request.body['cred_name'],
                              config.configFromStream(open('/tmp/machine.conf'),
                                                      base=config.configFromMap(request.body['conf'])))
                              

    cluster = cluster.update(startTask=request.body['task_name'])

    credClient = cred_client.CredentialClient(cluster.credName,
                                              request.mq,
                                              request.state.conf)

    try:
        cluster = yield start.startMaster(request.state, credClient, request.body['task_name'], cluster)
    except Exception, err:
        reactor.callLater(REMOVE_CLUSTER_TIMEOUT,
                          deleteCluster,
                          credClient,
                          request.body['cluster'],
                          request.body['user_name'])
        raise

        
    if request.body['num_exec'] > 0 or request.body['num_data'] > 0:
        addInstancesTaskName = yield clusters_client_www.addInstances('localhost',
                                                                      request.body['cluster'],
                                                                      request.body['user_name'],
                                                                      request.body['num_exec'],
                                                                      request.body['num_data'])

        localTask = yield tasks_tx.loadTask(request.body['task_name'])
        addInstanceState, addInstanceTask = yield tasks_tx.blockOnTaskAndForward('localhost',
                                                                                 request.body['cluster'],
                                                                                 addInstancesTaskName,
                                                                                 localTask)

        
    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.setState(task.TASK_COMPLETED).progress())

    defer.returnValue(request)

@defer_utils.timeIt
@defer.inlineCallbacks
def handleTaskTerminateCluster(request):
    # Start task running
    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.setState(task.TASK_RUNNING))

    if request.body['cluster'] != 'local':
        # If we are terminating a remote cluster
        cluster = yield persist.loadCluster(request.body['cluster'], request.body['user_name'])        
        credClient = cred_client.CredentialClient(cluster.credName,
                                                  request.mq,
                                                  request.state.conf)
        
        try:
            if cluster.master:
                taskName = yield clusters_client_www.terminateCluster(cluster.master['public_dns'],
                                                                      'local',
                                                                      None)
                yield tasks_tx.loadTask(request.body['task_name']
                                        ).addCallback(lambda t :
                                                      tasks_tx.blockOnTaskAndForward('localhost',
                                                                                     request.body['cluster'],
                                                                                     taskName,
                                                                                     t))
            cluster = cluster.setState(cluster.TERMINATED)
        except:
            cluster = yield terminateCluster(credClient, request.body['cluster'], request.body['user_name'])

        yield saveCluster(cluster, request.state)
        reactor.callLater(REMOVE_CLUSTER_TIMEOUT,
                          deleteCluster,
                          credClient,
                          cluster.clusterName,
                          cluster.userName)
    else:
        credClient = cred_client.CredentialClient('local',
                                                  request.mq,
                                                  request.state.conf)
        cluster = yield terminateCluster(credClient, 'local', request.body['user_name'])



    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.progress())

    defer.returnValue(request)

@defer_utils.timeIt
@defer.inlineCallbacks
def handleTaskTerminateInstances(request):
    # Start task running
    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.setState(task.TASK_RUNNING))

    
    if request.body['cluster'] != 'local':
        cluster = yield persist.loadCluster(request.body['cluster'], request.body['user_name'])
        credClient = cred_client.CredentialClient(cluster.credName,
                                                  request.mq,
                                                  request.state.conf)
        try:
            yield clusters_client_www.terminateInstances(cluster.master['public_dns'],
                                                         'local',
                                                         request.body['user_name'],
                                                         request.body['by_criteria'],
                                                         request.body['criteria_values'])
                
            taskName = yield tasks_tx.loadTask(request.body['task_name'])
            yield tasks_tx.loadTask(request.body['task_name']
                                    ).addCallback(lambda t :
                                                  tasks_tx.blockOnTaskAndForward('localhost',
                                                                                 request.body['cluster'],
                                                                                 taskName,
                                                                                 t))

        except:
            yield terminateInstancesByCriteria(credClient,
                                               request.body['cluster'],
                                               request.body['user_name'],
                                               request.body['by_criteria'],
                                               request.body['criteria_values'])
            
    else:
        cluster = yield persist.loadCluster('local', None)
        credClient = cred_client.CredentialClient(cluster.credName,
                                                  request.mq,
                                                  request.state.conf)        
        yield terminateInstancesByCriteria(credClient,
                                           'local',
                                           None,
                                           request.body['by_criteria'],
                                           request.body['criteria_values'])

    defer.returnValue(request)

@defer_utils.timeIt
@defer.inlineCallbacks
def handleTaskAddInstances(request):
    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.setState(task.TASK_RUNNING))


    cluster = yield persist.loadCluster('local', None)

    credClient = cred_client.CredentialClient(cluster.credName,
                                              request.mq,
                                              request.state.conf)

    cType = yield credClient.getCType()

    if cType != 'local':
        if request.body['num_exec'] > 0:
            yield start.startExecNodes(request.state,
                                       credClient,
                                       request.body['task_name'],
                                       request.body['num_exec'],
                                       cluster)

    defer.returnValue(request)

@defer_utils.timeIt
@defer.inlineCallbacks
def removeDeadClusters(mq, conf):
    clusters = yield persist.loadClustersAdmin()
    clusters = [c for c in clusters if c.state in [c.FAILED, c.TERMINATED]]

    for c in clusters:
        credClient = cred_client.CredentialClient(c.credName,
                                                  mq,
                                                  conf)
        yield deleteCluster(credClient, c.clusterName, c.userName)

    defer.returnValue(None)

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
@defer_utils.timeIt
def handleWWWClusterInfo(request):
    if request.body['cluster'] == 'local' and ('local', None) in request.state.clustersCache:
        return defer_pipe.ret(request.update(response=persist.clusterToDict(request.state.clustersCache[('local', None)])))
    elif (request.body['cluster'], request.body['user_name']) in request.state.clustersCache:
        response = persist.clusterToDict(request.state.clustersCache[(request.body['cluster'],
                                                                                    request.body['user_name'])])
        return defer_pipe.ret(request.update(response=response))
    else:
        raise Error('Cluster not found - %r' % request.body['cluster'])

@defer_utils.timeIt
@defer.inlineCallbacks
def handleWWWListClusters(request):
    clusters = yield persist.loadAllClusters(request.body['user_name'])
    clusterDicts = [persist.clusterToDict(c) for c in clusters]
    defer.returnValue(request.update(response=clusterDicts))

@defer_utils.timeIt
@defer.inlineCallbacks
def handleWWWConfigCluster(request):
    cluster = yield persist.loadCluster(request.body['cluster'], request.body['user_name'])
    js = json.dumps(cluster.config)
    defer.returnValue(request.update(response=js))

@defer_utils.timeIt
@defer.inlineCallbacks
def loadLocalCluster(mq, state):
    """If local cluster is not present, load it"""

    @defer.inlineCallbacks
    def _updateCluster(cluster):
        conf = config.configFromMap({'config_loaded': True},
                                    base=config.configFromStream(open('/tmp/machine.conf'),
                                                                 base=config.configFromEnv()))

        # Possible our IP has changed, let's update the master
        if cluster.credName == 'local' and conf('MASTER_IP') not in [cluster.master['public_dns'], cluster.master['private_dns']]:
            master = dict(instance_id='local',
                          ami_id=None,
                          public_dns=conf('MASTER_IP'),
                          private_dns=conf('MASTER_IP'),
                          state='running',
                          key=None,
                          index=None,
                          instance_type=None,
                          launch=None,
                          availability_zone=None,
                          monitor=None,
                          spot_request_id=None,
                          bid_price=None)

            cluster = cluster.setMaster(master).update(config=conf)
            yield persist.saveCluster(cluster)
            defer.returnValue(cluster)
        else:
            defer.returnValue(cluster)

    @defer.inlineCallbacks
    def _createCredentials():
        if os.path.exists('/tmp/cred-info'):
            cert, pkey, ctype, metadata = open('/tmp/cred-info').read().split('\t')
            yield cred_client.saveCredential('local',
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
                        raise Error('Instance list empty')
                    else:
                        return instances

                liDefer.addCallback(_failIfEmpty)
                return liDefer
            
            instances = yield defer_utils.tryUntil(10, _listInstances, onFailure=defer_utils.sleep(10))
            defer.returnValue(instances)
        else:
            yield cred_client.saveCredential('local',
                                             'Local credential',
                                             'local',
                                             None,
                                             None,
                                             {},
                                             config.configFromMap({}))
            defer.returnValue([])
        
    
    try:
        cluster = yield persist.loadCluster('local', None)
        cluster = yield _updateCluster(cluster)
        defer.returnValue(cluster)
    except persist.ClusterNotFoundError:
        instances = yield _createCredentials()

        cluster = persist.Cluster('local',
                                  None,
                                  'local',
                                  config.configFromMap({'config_loaded': True},
                                                       base=config.configFromStream(open('/tmp/machine.conf'), base=config.configFromEnv())))

        startTaskName = yield tasks_tx.createTaskAndSave('startCluster', 1)
        yield tasks_tx.updateTask(startTaskName,
                                  lambda t : t.setState(task.TASK_COMPLETED).progress())
        cluster = cluster.update(startTask=startTaskName)
        
        masterIdx = func.find(lambda i : cluster.config('MASTER_IP') in [i['public_dns'], i['private_dns']],
                              instances)

        if masterIdx is not None:
            master = instances[masterIdx]
        else:
            master = dict(instance_id='local',
                          ami_id=None,
                          public_dns=cluster.config('MASTER_IP'),
                          private_dns=cluster.config('MASTER_IP'),
                          state='running',
                          key=None,
                          index=None,
                          instance_type=None,
                          launch=None,
                          availability_zone=None,
                          monitor=None,
                          spot_request_id=None,
                          bid_price=None)
            
        cluster = cluster.setMaster(master)
        cluster = cluster.setState(cluster.RUNNING)
        yield persist.saveCluster(cluster)
        defer.returnValue(cluster)

def forwardOrCreate(url, dstQueue, tType, numTasks):
    return defer_pipe.runPipeCurry(defer_pipe.pipe([queue.forwardRequestToCluster(url),
                                                    queue.createTaskAndForward(dstQueue,
                                                                               tType,
                                                                               numTasks)]))


def returnClusterStartTaskIfExists(request):
    d = persist.loadCluster(request.body['cluster'], request.body['user_name'])

    def _exists(cl):
        if cl.state in [cl.TERMINATED, cl.FAILED]:
            raise persist.ClusterNotFoundError(cl.clusterName)
        else:
            request.body['task_name'] = cl.startTask
            return defer_pipe.emit(request.update(response=cl.startTask))

    def _doesNotExist(f):
        f.trap(persist.ClusterNotFoundError)
        return defer_pipe.ret(request)

    d.addCallback(_exists)
    d.addErrback(_doesNotExist)

    return d


def subscribeStartCluster(mq, state):
    conf = state.conf

    processStartClusterRequest = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                         'user_name',
                                                                                         'num_exec',
                                                                                         'num_data',
                                                                                         'cred_name']),
                                                                       returnClusterStartTaskIfExists,
                                                                       queue.createTaskAndForward(
                                                                           conf('clusters.startcluster_queue'),
                                                                           'startCluster',
                                                                           0)]))
                                                                       
    queue.subscribe(mq,
                    conf('clusters.startcluster_www'),
                    conf('clusters.concurrent_startcluster'),
                    queue.wrapRequestHandler(state, processStartClusterRequest))

    queue.subscribe(mq,
                    conf('clusters.startcluster_queue'),
                    conf('clusters.concurrent_startcluster'),
                    queue.wrapRequestHandlerTask(state, handleTaskStartCluster))
    

def subscribeTerminateCluster(mq, state):
    conf = state.conf

    processTerminateClusterRequest = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                             'user_name']),
                                                                           queue.createTaskAndForward(
                                                                               conf('clusters.terminatecluster_queue'),
                                                                               'terminateCluster',
                                                                               1)]))

    queue.subscribe(mq,
                    conf('clusters.terminatecluster_www'),
                    conf('clusters.concurrent_terminatecluster'),
                    queue.wrapRequestHandler(state, processTerminateClusterRequest))

    queue.subscribe(mq,
                    conf('clusters.terminatecluster_queue'),
                    conf('clusters.concurrent_terminatecluster'),
                    queue.wrapRequestHandlerTask(state, handleTaskTerminateCluster))


def subscribeTerminateInstances(mq, state):
    conf = state.conf

    processTerminateInstancesRequest = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                               'user_name',
                                                                                               'by_criteria',
                                                                                               'criteria_values']),
                                                                             queue.createTaskAndForward(
                                                                                 conf('clusters.terminateinstances_queue'),
                                                                                 'terminateInstances',
                                                                                 1)]))
    
    queue.subscribe(mq,
                    conf('clusters.terminateinstances_www'),
                    conf('clusters.concurrent_terminateinstances'),
                    queue.wrapRequestHandler(state, processTerminateInstancesRequest))

    queue.subscribe(mq,
                    conf('clusters.terminateinstances_queue'),
                    conf('clusters.concurrent_terminateinstances'),
                    queue.wrapRequestHandlerTask(state, handleTaskTerminateInstances))

def subscribeAddInstances(mq, state):
    conf = state.conf

    processAddInstancesRequest = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                         'user_name',
                                                                                         'num_data',
                                                                                         'num_exec']),
                                                                       forwardOrCreate(
                                                                           conf('www.url_prefix') + '/' +
                                                                           os.path.basename(conf('clusters.addinstances_www')),
                                                                           conf('clusters.addinstances_queue'),
                                                                           'addInstances',
                                                                           0)]))

    queue.subscribe(mq,
                    conf('clusters.addinstances_www'),
                    conf('clusters.concurrent_addinstances'),
                    queue.wrapRequestHandler(state, processAddInstancesRequest))

    queue.subscribe(mq,
                    conf('clusters.addinstances_queue'),
                    conf('clusters.concurrent_addinstances'),
                    queue.wrapRequestHandlerTask(state, handleTaskAddInstances))

    
def subscribeToQueues(mq, state):
    subscribeStartCluster(mq, state)
    subscribeTerminateCluster(mq, state)
    subscribeTerminateInstances(mq, state)
    subscribeAddInstances(mq, state)
    clusters_cleanup.subscribe(mq, state)
    
    #
    # These return immediatly
    processClusterInfo = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                 'user_name']),
                                                               handleWWWClusterInfo]))
                                             

    queue.subscribe(mq,
                    state.conf('clusters.clusterinfo_www'),
                    state.conf('clusters.concurrent_clusterinfo'),
                    queue.wrapRequestHandler(state, processClusterInfo))
                    


    processListClusters = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['user_name']),
                                                                handleWWWListClusters]))

    queue.subscribe(mq,
                    state.conf('clusters.listclusters_www'),
                    state.conf('clusters.concurrent_listclusters'),
                    queue.wrapRequestHandler(state, processListClusters))
                    

    
    processConfigCluster = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                   'user_name']),
                                                                 handleWWWConfigCluster]))

    queue.subscribe(mq,
                    state.conf('clusters.listclusters_www'),
                    state.conf('clusters.concurrent_listclusters'),
                    queue.wrapRequestHandler(state, processConfigCluster))
                    

def makeService(conf):
    mqService = client.makeService(conf)

    mqFactory = mqService.mqFactory

    # State is currently not used, but kept around for future purposes
    state = State(conf)

    # Startup list
    startUpDefer = loadLocalCluster(mqFactory, state)
    startUpDefer.addCallback(lambda _ : removeDeadClusters(mqFactory, conf))
    startUpDefer.addCallback(lambda _ : refreshClusters(mqFactory, state))
    startUpDefer.addCallback(lambda _ : subscribeToQueues(mqFactory, state))

    return mqService

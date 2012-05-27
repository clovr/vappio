from twisted.internet import defer

from twisted.python import log

from igs.utils import config

from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.clusters import persist
from vappio_tx.clusters import instance_flow

from vappio_tx.internal_client import credentials as cred_client

from vappio_tx.www_client import clusters as clusters_client_www

@defer.inlineCallbacks
def returnClusterStartTaskIfExists(request):
    persistManager = request.state.persistManager

    try: 
        cluster = yield persistManager.loadCluster(request.body['cluster_name'],
                                                   request.body['user_name'])

        if cluster.state in [cluster.TERMINATED, cluster.FAILED]:
            defer.returnValue(request)
        else:
            request.body['task_name'] = cluster.startTask
            defer_pipe.emit(request.update(response=cluster.startTask))
    except persist.ClusterNotFoundError:
        defer.returnValue(request)


@defer_utils.timeIt
@defer.inlineCallbacks
def _handleStartCluster(request):
    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.setState(tasks_tx.task.TASK_RUNNING))

    baseConf = config.configFromStream(open('/tmp/machine.conf'))
    cluster = persist.Cluster(request.body['cluster_name'],
                              request.body['user_name'],
                              request.body['cred_name'],
                              config.configFromMap(request.body['conf'],
                                                   base=baseConf))

    cluster = cluster.update(startTask=request.body['task_name'])

    credClient = cred_client.CredentialClient(cluster.credName,
                                              request.mq,
                                              request.state.conf)

    
    try:
        cluster = yield instance_flow.startMaster(request.state,
                                                  credClient,
                                                  request.body['task_name'],
                                                  cluster)
    except Exception, err:
        log.err('Start cluster failed')
        log.err(err)
        cluster = yield request.state.persistManager.loadCluster(request.body['cluster_name'],
                                                                 request.body['user_name'])
        cluster = cluster.setState(cluster.FAILED)
        yield defer_utils.sleep(120)()
        yield request.state.persistManager.removeCluster(request.body['cluster_name'],
                                                         request.body['user_name'])
        raise err


    if request.body['num_exec'] > 0 or request.body['num_data'] > 0:
        addInstancesTaskName = yield clusters_client_www.addInstances('localhost',
                                                                      request.body['cluster_name'],
                                                                      request.body['user_name'],
                                                                      request.body['num_exec'],
                                                                      request.body['num_data'])
        localTask = yield tasks_tx.loadTask(request.body['task_name'])
        yield tasks_tx.blockOnTaskForward('localhost',
                                          request.body['cluster_name'],
                                          addInstancesTaskName,
                                          localTask)
    
    defer.returnValue(request)


@defer.inlineCallbacks
def handleStartCluster(request):
    ret = yield request.state.clusterLocks.run((request.body['cluster_name'],
                                                request.body['user_name']),
                                               _handleStartCluster,
                                               request)
    defer.returnValue(ret)


def subscribe(mq, state):
    createAndForward = queue.createTaskAndForward(state.conf('clusters.startcluster_queue'),
                                                  'startCluster',
                                                  0)

    processStartPipe = defer_pipe.pipe([queue.keysInBody(['cluster_name',
                                                          'user_name',
                                                          'num_exec',
                                                          'num_data',
                                                          'cred_name',
                                                          'conf']),
                                        returnClusterStartTaskIfExists,
                                        createAndForward])
    
    processStartCluster = queue.returnResponse(processStartPipe)

    queue.subscribe(mq,
                    state.conf('clusters.startcluster_www'),
                    state.conf('clusters.concurrent_startcluster'),
                    queue.wrapRequestHandler(state, processStartCluster))

    queue.subscribe(mq,
                    state.conf('clusters.startcluster_queue'),
                    state.conf('clusters.concurrent_startcluster'),
                    queue.wrapRequestHandlerTask(state, handleStartCluster))

from twisted.internet import defer

from igs.utils import auth_token
from igs.utils import errors
from igs.utils import functional as func

from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.internal_client import credentials as cred_client

from vappio_tx.www_client import clusters as clusters_client_www

REMOVE_CLUSTER_TIMEOUT = 120

@defer.inlineCallbacks
def terminateRemoteCluster(request, authToken):
    persistManager = request.state.persistManager

    cluster = yield persistManager.loadCluster(request.body['cluster_name'],
                                               request.body['user_name'])
    credClient = cred_client.CredentialClient(cluster.credName,
                                              request.mq,
                                              request.state.conf)

    try:
        if cluster.master:
            terminateCluster = clusters_client_www.terminateCluster
            remoteTaskName = yield terminateCluster(cluster.master['public_dns'],
                                                    'local',
                                                    None,
                                                    authToken)
            localTask = yield tasks_tx.loadTask(request.body['task_name'])
            yield tasks_tx.blockOnTaskAndForward('localhost',
                                                 request.body['cluster_name'],
                                                 remoteTaskName,
                                                 localTask)

    except errors.RemoteError, err:
        # If the error is not an auth token one then kill it
        # otherwise it means we think we own a cluster that
        # we don't
        #
        # In this case another part of the system is in charge
        # of forgetting about the clusters we shouldn't know
        if err.name != 'igs.utils.auth_token.AuthTokenError':
            yield terminateCluster(credClient,
                                   request.body['cluster_name'],
                                   request.body['user_name'])
        else:
            raise
    except:
        # Any other random error means we have to try to kill
        yield terminateCluster(credClient,
                               request.body['cluster_name'],
                               request.body['user_name'])
        
    defer.returnValue(cluster.setState(cluster.TERMINATED))


@defer.inlineCallbacks
def terminateCluster(credClient, persistManager, clusterName, userName):
    cluster = yield persistManager.loadCluster(clusterName, userName)

    yield defer_utils.mapSerial(lambda instances :
                                    credClient.terminateInstances(instances),
                                func.chunk(5, cluster.execNodes + cluster.dataNodes))

    if cluster.master:
        yield credClient.terminateInstances([cluster.master])

    defer.returnValue(cluster.setState(cluster.TERMINATED))

    
@defer_utils.timeIt
@defer.inlineCallbacks
def _handleTerminateCluster(request):
    # Start task running
    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.setState(tasks_tx.task.TASK_RUNNING))

    persistManager = request.state.persistManager
    
    authToken = auth_token.generateToken(request.state.machineConf)
    
    if request.body['cluster_name'] != 'local':
        cluster = yield terminateRemoteCluster(request, authToken)
        yield persistManager.saveCluster(cluster)

        yield defer_utils.sleep(REMOVE_CLUSTER_TIMEOUT)()
        yield persistManager.removeCluster(request.body['cluster_name'],
                                           request.body['user_name'])

    else:
        if ('auth_token' in request.body and
            request.body['auth_token'] == authToken):
            credClient = cred_client.CredentialClient('local',
                                                      request.mq,
                                                      request.state.conf)
            yield terminateCluster(credClient,
                                   'local',
                                   request.body['user_name'])
        else:
            raise auth_token.AuthTokenError()

    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.progress())

    defer.returnValue(request)

@defer_utils.timeIt
@defer.inlineCallbacks
def handleTerminateCluster(request):
    ret = yield request.state.clusterLocks.run((request.body['cluster_name'],
                                                request.body['user_name']),
                                               _handleTerminateCluster,
                                               request)
    defer.returnValue(ret)


def subscribe(mq, state):
    createAndForward = queue.createTaskAndForward(state.conf('clusters.terminatecluster_queue'),
                                                  'terminateCluster',
                                                  1)
    processTerminatePipe = defer_pipe.pipe([queue.keysInBody(['cluster_name',
                                                              'user_name']),
                                            createAndForward])
    
    processTerminateCluster = queue.returnResponse(processTerminatePipe)

    queue.subscribe(mq,
                    state.conf('clusters.terminatecluster_www'),
                    state.conf('clusters.concurrent_terminatecluster'),
                    queue.wrapRequestHandler(state, processTerminateCluster))

    queue.subscribe(mq,
                    state.conf('clusters.terminatecluster_queue'),
                    state.conf('clusters.concurrent_terminatecluster'),
                    queue.wrapRequestHandlerTask(state, handleTerminateCluster))
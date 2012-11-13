from twisted.internet import defer

from twisted.python import log

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
def removeTerminatedCluster(persistManager, credClient, clusterName, userName):
    yield defer_utils.sleep(REMOVE_CLUSTER_TIMEOUT)()
    cluster = yield persistManager.loadCluster(clusterName, userName)
        
    if cluster.state == cluster.TERMINATED:
        # Another check to make sure the instances have
        # really been terminated
        instances = ([cluster.master] +
                     cluster.execNodes +
                     cluster.dataNodes)

        instances = yield credClient.updateInstances(instances)

        undeadInstances = [i
                           for i in instances
                           if i['state'] != 'terminated']
        
        if undeadInstances:
            yield defer_utils.mapSerial(lambda instances :
                                            credClient.terminateInstances(instances),
                                        func.chunk(5, undeadInstances))
            
        yield persistManager.removeCluster(clusterName, userName)
    

@defer.inlineCallbacks
def terminateCluster(credClient, persistManager, clusterName, userName):
    cluster = yield persistManager.loadCluster(clusterName, userName)

    yield defer_utils.mapSerial(lambda instances :
                                    credClient.terminateInstances(instances),
                                func.chunk(5, cluster.execNodes + cluster.dataNodes))

    if cluster.master:
        yield credClient.terminateInstances([cluster.master])

    defer.returnValue(cluster.setState(cluster.TERMINATED))

@defer.inlineCallbacks
def terminateRemoteCluster(request):
    persistManager = request.state.persistManager

    cluster = yield persistManager.loadCluster(request.body['cluster_name'],
                                               request.body['user_name'])
    authToken = auth_token.generateToken(cluster.config('cluster.cluster_public_key'))

    credClient = cred_client.CredentialClient(cluster.credName,
                                              request.mq,
                                              request.state.conf)

    try:
        if cluster.master:
            wwwTerminateCluster = clusters_client_www.terminateCluster
            remoteTaskName = yield wwwTerminateCluster(cluster.master['public_dns'],
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
            log.err(err)
            yield terminateCluster(credClient,
                                   persistManager,
                                   request.body['cluster_name'],
                                   request.body['user_name'])
        else:
            raise
    except Exception, err:
        log.err(err)
        # Any other random error means we have to try to kill
        yield terminateCluster(credClient,
                               persistManager,
                               request.body['cluster_name'],
                               request.body['user_name'])
        
    defer.returnValue(cluster.setState(cluster.TERMINATED))

    
@defer_utils.timeIt
@defer.inlineCallbacks
def _handleTerminateCluster(request):
    # Start task running
    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.setState(tasks_tx.task.TASK_RUNNING))

    persistManager = request.state.persistManager
    
    credClient = cred_client.CredentialClient('local',
                                              request.mq,
                                              request.state.conf)    
    if request.body['cluster_name'] != 'local':
        cluster = yield terminateRemoteCluster(request)
        yield persistManager.saveCluster(cluster)

        removeTerminatedCluster(persistManager,
                                credClient,
                                request.body['cluster_name'],
                                request.body['user_name'])

    else:
        ctype = yield credClient.getCType()

        if ctype == "local":
            ## Push through terminate (should be a NOOP)
            yield terminateCluster(credClient,
                                   persistManager,
                                   'local',
                                   request.body['user_name'])
        elif ('auth_token' in request.body and 
             auth_token.validateToken(request.body['auth_token'])):
            yield terminateCluster(credClient,
                                   persistManager,
                                   'local',
                                   request.body['user_name'])
            removeTerminatedCluster(persistManager,
                                    credClient,
                                    request.body['cluster_name'],
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

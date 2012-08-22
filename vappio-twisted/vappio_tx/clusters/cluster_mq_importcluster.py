"""
Handles importing clusters from a remote VM with proper authorization

"""

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

@defer.inlineCallbacks
def returnClusterImportTaskIfExists(request):
    """
    Returns the task name of the import cluster operation if it exists 
    already.

    """
    ## TODO: Hook this into the main import pipeline.
    persistManager = request.state.persistManager
    
    try:
        # Going to be injecting values into the request body instead of just
        # directly specifying 'None' for our user name here
        cluster = yield persistManager.loadCluster(request.body['dst_cluster'],
                                                   request.body['user_name'])

        if cluster.state in [cluster.TERMINATED, cluster.FAILED]:
            defer.returnValue(request)
        else:
            # Do we want to lump this into the startTask or create a new
            # importTask attribute?
            request.body['task_name'] = cluster.importTask
            defer_pipe.emit(request.update(response=cluster.importTask))
    except persist.ClusterNotFoundError:
        defer.returnValue(request)

@defer.inlineCallbacks
def createCluster(request):
    persistManager = request.state.persistManager
    
    cluster = persist.Cluster(request.body['dst_cluster'],
                              request.body['user_name'],
                              request.body['cred_name'],
                              config.configFromStream(open('/tmp/machine.conf')))

    yield persistManager.saveCluster(cluster)
    defer.returnValue(request)

@defer_utils.timeIt
@defer.inlineCallbacks
def _handleImportCluster(request):
    """Imports a VM found on a remote host."""
    persistManager = request.state.persistManager

    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t: t.setState(tasks_tx.task.TASK_RUNNING))

    cluster = yield request.state.persistManager.loadCluster(request.body['dst_cluster'],
                                                             request.body['user_name'])

    cluster = cluster.update(startTask=request.body['task_name'])

    credClient = cred_client.CredentialClient(cluster.credName,
                                              request.mq,
                                              request.state.conf)

    try:
        cluster = yield instance_flow.importCluster(request.state,
                                                    credClient,
                                                    request.body['task_name'],
                                                    request.body['host'],
                                                    request.body['src_cluster'],
                                                    cluster)

    except Exception, err:
        # If we have an authentication error we want to indicate that and 
        # die immediately
        #if err.name == 'igs.utils.auth_token.AuthTokenError': 
        #    log.err('IMPORTCLUSTER: Authorization failed')
        #else:
        log.err('IMPORTCLUSTER: Failed')                                

        log.err(err)

        cluster = yield request.state.persistManager.loadCluster(request.body['dst_cluster'],
                                                                 request.body['user_name'])
        cluster = cluster.setState(cluster.FAILED)
        yield defer_utils.sleep(120)()
        yield request.state.persistManager.removeCluster(request.body['dst_cluster'],
                                                         request.body['user_name'])

    defer.returnValue(request)

@defer.inlineCallbacks
def handleImportCluster(request):
    """
    Kicks off the import cluster workflow via the cluster locking mechanism
    
    """
    ret = yield request.state.clusterLocks.run((request.body['dst_cluster'],
                                                request.body['user_name']),
                                               _handleImportCluster,
                                               request)
    defer.returnValue(ret)

def subscribe(mq, state):
    """
    Subscribes to the queues needed to handle any incoming import cluster 
    requests.

    """
    # How many steps do we need for this task?
    createAndForward = queue.createTaskAndForward(state.conf('clusters.importcluster_queue'),
                                                  'importCluster',
                                                  3)

    processImportPipe = defer_pipe.pipe([queue.keysInBody(['host',
                                                           'cred_name',
                                                           'user_name',
                                                           'src_cluster',
                                                           'dst_cluster']),
                                        #returnClusterImportTaskIfExists,
                                        createCluster,
                                        createAndForward])

    processImportCluster = queue.returnResponse(processImportPipe)

    queue.subscribe(mq,
                    state.conf('clusters.importcluster_www'),
                    state.conf('clusters.concurrent_importcluster'),
                    queue.wrapRequestHandler(state, processImportCluster))

    queue.subscribe(mq,
                    state.conf('clusters.importcluster_queue'),
                    state.conf('clusters.concurrent_importcluster'),
                    queue.wrapRequestHandlerTask(state, handleImportCluster))



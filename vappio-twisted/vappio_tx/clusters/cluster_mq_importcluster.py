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
    """Returns the task name of the import cluster operation if it exists 
    already.

    """
    persistManager = request.state.persistManager
    
    try:
        cluster = yield persistManager.loadCluster(request.body['dst_cluster'],
                                                   request.body['user_name'])

        if cluster.state in [cluster.TERMINATED, cluster.FAILED]:
            defer.returnValue(request)
        else:
            # We won't really have an importTask attribute here but will 
            # instead lump the task name under the startTask attribute
            request.body['task_name'] = cluster.startTask
            defer_pipe.emit(request.update(response=cluster.startTask))
    except persist.ClusterNotFoundError:
        defer.returnValue(request)

@defer.inlineCallbacks
def createCluster(request):
    """Instantiates a skeleton of the cluster that will be imported. This 
    cluster will later have the proper attributes and values populated from
    the source cluster.
    
    """
    persistManager = request.state.persistManager
 
    baseConf = config.configFromStream(open('/tmp/machine.conf'))
    cluster = persist.Cluster(request.body['dst_cluster'],
                              request.body['user_name'],
                              request.body['cred_name'],
                              config.configFromMap({'cluster.cluster_public_key': '/home/www-data/.ssh/id_rsa.pub'},
                                                   base=baseConf))

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
        if err.name == 'igs.utils.auth_token.AuthTokenError': 
            log.err('IMPORTCLUSTER: Authorization failed')
        else:
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
    """Kicks off the import cluster workflow using the cluster locking 
    mechanism.
    
    """
    ret = yield request.state.clusterLocks.run((request.body['dst_cluster'],
                                                request.body['user_name']),
                                               _handleImportCluster,
                                               request)
    defer.returnValue(ret)

def subscribe(mq, state):
    """Subscribes to the queues needed to handle any incoming import cluster 
    requests.

    """
    createAndForward = queue.createTaskAndForward(state.conf('clusters.importcluster_queue'),
                                                  'importCluster',
                                                  4)

    processImportPipe = defer_pipe.pipe([queue.keysInBody(['host',
                                                           'cred_name',
                                                           'user_name',
                                                           'src_cluster',
                                                           'dst_cluster']),
                                        returnClusterImportTaskIfExists,
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

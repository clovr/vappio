from twisted.internet import defer

from igs_tx.utils import defer_utils
from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue


@defer_utils.timeIt
@defer.inlineCallbacks
def handleConfig(request):
    """
    Returns the config for a single cluster in the system.
    Throws an error if the cluster is not found.
    
    Input:
    { cluster_name   : string
      user_name      : string
    }

    Output:
    config - keyvalues
    """
    persistManager = request.state.persistManager
    cluster = yield persistManager.loadCluster(request.body['cluster_name'],
                                               request.body['user_name'])[0]
    clusterDict = persistManager.clusterToDict(cluster)
    defer.returnValue(request.update(response=clusterDict['config']))


def subscribe(mq, state):
    processPipe = defer_pipe.pipe([queue.keysInBody(['user_name',
                                                     'cluster_name']),
                                   handleConfig])
    processClusterConfig = queue.returnResponse(processPipe)
    queue.subscribe(mq,
                    state.conf('clusters.config_www'),
                    state.conf('clusters.concurrent_config'),
                    queue.wrapRequestHandler(state, processClusterConfig))

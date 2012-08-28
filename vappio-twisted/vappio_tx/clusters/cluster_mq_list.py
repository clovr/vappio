from twisted.internet import defer

from igs.utils import auth_token

from igs_tx.utils import defer_utils
from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

def removeDetail(cluster):
    """Currently does nothing"""
    return cluster

@defer_utils.timeIt
@defer.inlineCallbacks
def handleList(request):
    """
    Requires a user_name, can take a criteria to narrow
    the cluster search by.  Takes a list of strings for
    other options.  Currently the only other option is
    to turn return lite clusters.

    Input:
    { user_name : string
      ?criteria : string
      ?options  : {'lite'       : boolean,
                   'auth_token' : string
                  }
    }
    Output:
    [cluster] | [cluster_lite]
    """
    if 'auth_token' in request.body.get('options', {}):
        authToken = request.body['options']['auth_token']
        if not auth_token.validateToken(authToken):
            raise auth_token.AuthTokenError()
        
    persistManager = request.state.persistManager
    clusters = yield persistManager.loadClustersBy(request.body.get('criteria', {}),
                                                   request.body['user_name'])
    clusterDicts = map(persistManager.clusterToDict, clusters)
    if request.body.get('options', {}).get('lite', False):
        clusterDicts = map(removeDetail, clusterDicts)
        
    defer.returnValue(request.update(response=clusterDicts))

def subscribe(mq, state):
    processPipe = defer_pipe.pipe([queue.keysInBody(['user_name']),
                                   handleList])
    processClusterList = queue.returnResponse(processPipe)
    queue.subscribe(mq,
                    state.conf('clusters.listclusters_www'),
                    state.conf('clusters.concurrent_listclusters'),
                    queue.wrapRequestHandler(state, processClusterList))

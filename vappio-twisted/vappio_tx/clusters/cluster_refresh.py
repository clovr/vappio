from twisted.internet import defer
from twisted.internet import reactor

from twisted.python import log

from igs.utils import errors
from igs.utils import auth_token

from igs_tx.utils import defer_utils

from vappio_tx.www_client import clusters as clusters_www_client

CLUSTER_REFRESH_FREQUENCY = 30

@defer_utils.timeIt
@defer.inlineCallbacks
def loadRemoteCluster(state, cl):
    """
    Tries to load a cluster.  Returns the cluster on success
    otherwise throws an error.

    If the cluster is not actually owned by us throws
    auth_token.AuthTokenError

    If it's unresponsive throws
    errors.RemoteError
    """
    if cl.master:
        authToken = auth_token.generateToken(state.machineConf)

        try:
            clusters = yield clusters_www_client.listClusters(cl.master['public_dns'],
                                                              {'cluster_name': 'local'},
                                                              None,
                                                              authToken,
                                                              timeout=10,
                                                              tries=3)

            cluster = clusters[0]
            
            defer.returnValue(cluster)
        except errors.RemoteError, err:
            if err.name == 'igs.utils.auth_token.AuthTokenError':
                raise auth_token.AuthTokenError()
            else:
                raise

@defer.inlineCallbacks
def refreshClusters(mq, state):
    persistManager = state.persistManager

    try:
        clusters = yield persistManager.loadClustersByAdmin({})

        for cluster in clusters:
            try:
                if cluster.state in [cluster.RUNNING, cluster.UNRESPONSIVE]:
                    remoteCluster = yield loadRemoteCluster(state, cluster)
                    cluster = cluster.addExecNodes(remoteCluster['exec_nodes'])
                    cluster = cluster.addDataNodes(remoteCluster['data_nodes'])
                    cluster = cluster.setState(cluster.RUNNING)
                    yield persistManager.saveCluster(cluster)
            except auth_token.AuthTokenError:
                ## If we got an auth token error it means that
                ## a cluster we thought we owned isn't actually
                ## owned by us.  Let's log this information out
                ## and then remove it from our list.
                log.msg('AUTH_TOKEN_ERROR: Cluster: %s Master: %s' % (
                        cluster.clusterName,
                        cluster.master['public_dns']))
                yield persistManager.removeCluster(cluster.clusterName,
                                                   cluster.userName)
            except Exception, err:
                log.msg('REFRESH: Error')
                log.err(err)
                currCluster = yield persistManager.loadCluster(cluster.clusterName,
                                                               cluster.userName)

                ## The state of the cluster could have changed since
                ## we tried to access it
                if currCluster.state in [cluster.RUNNING, cluster.UNRESPONSIVE]:
                    cluster = cluster.setState(cluster.UNRESPONSIVE)
                    yield persistManager.saveCluster(cluster)

    except Exception, err:
        ## Incase anything goes wrong, try again
        log.msg('REFRESH: Error')
        log.err(err)
        
    reactor.callLater(CLUSTER_REFRESH_FREQUENCY, refreshClusters, mq, state)


def subscribe(mq, state):
    refreshClusters(mq, state)
    

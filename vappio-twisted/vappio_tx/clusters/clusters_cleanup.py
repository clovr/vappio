from twisted.internet import reactor
from twisted.internet import defer

from twisted.python import log

from vappio_tx.internal_client import clusters as clusters_client

# Refresh cluster information every sixty seconds
REFRESH_FREQUENCY = 60

# A cluster times out after an hour of unresponsiveness
CLUSTER_TIMEOUT = 60 * 60

def updateUnresponsiveClusters(clusterMap, clusters):
    ## Find all those clusters that are unresponsive
    unresponsiveClusters = [(cluster.clusterName, cluster.userName)
                            for cluster in clusters
                            if cluster.state == cluster.UNRESPONSIVE]

    ## Take the set of clusters we saw last iteration that were
    ## unresponsive and subtract from it the current set of
    ## unresponsive clusters.  The remainder is those clusters which
    ## either do not exist anymore or are no responsive again
    removeClusters = set(clusterMap.keys()) - set(unresponsiveClusters)

    ## Remove the clusters that are no longer unresponsive
    for c in removeClusters:
        clusterMap.pop()

    ## Update the amount of time that a cluster has been unresponsive.
    ## This assumes that this function runs ever REFRESH_FREQUENCY
    for c in unresponsiveClusters:
        v = clusterMap.get(c, 0)
        v += REFRESH_FREQUENCY
        clusterMap[c] = v

@defer.inlineCallbacks
def updateClusterInfo(state):
    try:
        clusters = yield state.persistManager.loadClustersByAdmin({})
        updateUnresponsiveClusters(state.unresponsiveClusters,
                                   clusters)

        for (clusterName, userName), duration in state.unresponsiveClusters.iteritems():
            if duration > CLUSTER_TIMEOUT:
                log.msg('CLEANUP: Terminating cluster - ' + clusterName)
                authToken = auth_token.generateToken(state.machineConf)
                yield clusters_client.terminateCluster(clusterName, userName, authToken)
    except Exception, err:
        log.err('CLEANUP: Failed')
        log.err(err)

    reactor.callLater(REFRESH_FREQUENCY, updateClusterInfo, state)

def subscribe(_mq, state):
    reactor.callLater(0.0, updateClusterInfo, state)

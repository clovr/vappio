from twisted.internet import reactor
from twisted.internet import defer

from twisted.python import log

from igs_tx.utils import defer_utils

from vappio_tx.internal_client import clusters as clusters_client

# Refresh cluster information every sixty seconds
REFRESH_FREQUENCY = 60

# A cluster times out after an hour of unresponsiveness
CLUSTER_TIMEOUT = 60 * 60

CLUSTER_USERNAME = 'guest'

def _updateUnresponsiveClusters(clusterMap, clusters):
    unresponsiveClusters = [c['cluster_name']
                            for c in clusters
                            if c['state'] == 'unresponsive']
    removeClusters = set(clusterMap.keys()) - set(unresponsiveClusters)
    
    for c in removeClusters:
        clusterMap.pop(c)

    for c in unresponsiveClusters:
        v = clusterMap.get(c, 0)
        v += REFRESH_FREQUENCY
        clusterMap[c] = v

@defer.inlineCallbacks
def _getClusters():
    clusters = yield defer_utils.tryUntil(10,
                                          lambda : clusters_client.listClusters(CLUSTER_USERNAME),
                                          onFailure=defer_utils.sleep(10))

    clustersDetail = yield defer_utils.mapSerial(lambda c : clusters_client.loadCluster(c['cluster_name'], CLUSTER_USERNAME),
                                                 clusters)
    defer.returnValue(clustersDetail)


@defer.inlineCallbacks
def _updateClusterInfoThrow(state):
    clusters = yield _getClusters()
    
    _updateUnresponsiveClusters(state.unresponsiveClusters, clusters)

    log.msg(state.unresponsiveClusters)
            
    for c, v in state.unresponsiveClusters.iteritems():
        if v > CLUSTER_TIMEOUT:
            log.msg('CLEANUP: Terminating cluster - ' + c)
            clusters_client.terminateCluster(c, CLUSTER_USERNAME)
    

@defer.inlineCallbacks
def _updateClusterInfo(state):
    log.msg('CLEANUP: Looping')
    try:
        yield _updateClusterInfoThrow(state)
    except Exception, err:
        log.err('CLEANUP: Failed')
        log.err(err)

    reactor.callLater(REFRESH_FREQUENCY, _updateClusterInfo, state)    
    

@defer.inlineCallbacks
def _initialClusterInfo(state):
    clusters = yield _getClusters()
    log.msg('CLEANUP: Loaded # clusters: %d' % len(clusters))

    _updateUnresponsiveClusters(state.unresponsiveClusters, clusters)
    
    reactor.callLater(REFRESH_FREQUENCY, _updateClusterInfo, state)

def subscribe(_mq, state):
    reactor.callLater(0.0, _initialClusterInfo, state)

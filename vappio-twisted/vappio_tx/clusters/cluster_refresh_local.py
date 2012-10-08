"""
Refreshes local clusters instances on a periodic basis.
"""

from twisted.internet import defer
from twisted.internet import reactor

from twisted.python import log

from vappio_tx.internal_client import credentials as cred_client

INSTANCE_REFRESH_FREQUENCY = 30

@defer.inlineCallbacks
def refreshInstances(mq, state):
    """Refreshes the local clusters instances (exec + data nodes). 
    
    Any instances that have been terminated, are unresponsive, or disappeared 
    since our last refresh are considered terminated and will be removed from 
    the local clusters instance list.
    
    """
    persistManager = state.persistManager
    updatedExecNodes = []
    updatedDataNodes = []

    try:
        cluster = yield persistManager.loadCluster('local', None)
        credClient = cred_client.CredentialClient(cluster.credName,
                                                  mq,
                                                  state.conf)

        # Want to make sure we only are doing this on running or unresponsive
        # clusters; terminated clusters will be cleaned up elsewhere
        if cluster.state in [cluster.RUNNING, cluster.UNRESPONSIVE]:
            clExecNodes = cluster.execNodes
            clDataNodes = cluster.dataNodes
        
            instances = yield credClient.updateInstances(clExecNodes + clDataNodes)
            updatedExecNodes.extend([x for x in instances if x in clExecNodes])
            updatedDataNodes.extend([x for x in instances if x in clDataNodes])
    
            cluster = cluster.updateExecNodes(updatedExecNodes)
            cluster = cluster.updateDataNodes(updatedDataNodes)

            yield persistManager.saveCluster(cluster)
    except Exception as err:
        log.msg('INSTANCES REFRESH: Error')
        log.err(err)

    reactor.callLater(INSTANCE_REFRESH_FREQUENCY, refreshInstances, mq, state)        

@defer.inlineCallbacks
def handleRefreshInstances(mq, state):
    ret = yield state.clusterLocks.run(('local', None),
                                       refreshInstances,
                                       mq,
                                       state)

    defer.returnValue(ret)

def subscribe(mq, state):
    """Subscribes to the proper queue to handle any incoming refresh instances
    requests.

    """
    handleRefreshInstances(mq, state)

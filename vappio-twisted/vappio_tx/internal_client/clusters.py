from vappio_tx.www_client import clusters

def loadCluster(clusterName, userName, timeout=30, tries=4):
    return clusters.loadCluster('localhost', clusterName, userName, timeout=timeout, tries=tries)

def listClusters(userName, timeout=30, tries=4):
    return clusters.listClusters('localhost',
                                 'local',
                                 userName,
                                 timeout=timeout,
                                 tries=tries)

def terminateCluster(clusterName, userName, timeout=30, tries=4):
    return clusters.terminateCluster('localhost',
                                     clusterName,
                                     userName,
                                     timeout=timeout,
                                     tries=tries)

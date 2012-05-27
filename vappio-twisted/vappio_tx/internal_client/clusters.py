from vappio_tx.www_client import clusters

def listClusters(criteria, userName, timeout=30, tries=4):
    return clusters.listClusters('localhost',
                                 criteria,
                                 userName,
                                 timeout=timeout,
                                 tries=tries)

def terminateCluster(clusterName, userName, authToken, timeout=30, tries=4):
    return clusters.terminateCluster('localhost',
                                     clusterName,
                                     userName,
                                     authToken,
                                     timeout=timeout,
                                     tries=tries)

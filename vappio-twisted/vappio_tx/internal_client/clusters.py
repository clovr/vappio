from vappio_tx.www_client import clusters

def loadCluster(clusterName, userName):
    return clusters.loadCluster('localhost', clusterName, userName)

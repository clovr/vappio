from igs_tx.utils import http

CLUSTERINFO_URL = '/vappio/clusterInfo_ws.py'
TERMINATECLUSTER_URL = '/vappio/terminateCluster_ws.py'

def loadCluster(host, clusterName, userName, timeout=30, tries=4):
    return http.performQuery(host,
                             CLUSTERINFO_URL,
                             dict(cluster=clusterName,
                                  user_name=userName),
                             timeout=timeout,
                             tries=tries)

def terminateCluster(host, clusterName, userName, timeout=30, tries=4):
    return http.performQuery(host,
                             TERMINATECLUSTER_URL,
                             dict(cluster=clusterName,
                                  user_name=userName),
                             timeout=timeout,
                             tries=tries)    

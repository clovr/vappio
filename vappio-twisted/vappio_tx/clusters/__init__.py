from igs_tx.utils import http

from vappio.cluster import control as cluster_control

CLUSTERINFO_URL = '/vappio/clusterInfo_ws.py'

def loadCluster(host, cluster, partial=False):
    d = http.performQuery(host, CLUSTERINFO_URL, dict(name=cluster,
                                                      partial=partial))
    d.addCallback(cluster_control.clusterFromDict)
    return d


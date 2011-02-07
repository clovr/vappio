from igs_tx.utils import http

CLUSTERINFO_URL = '/vappio/clusterInfo_ws.py'
TERMINATECLUSTER_URL = '/vappio/terminateCluster_ws.py'
TERMINATEINSTANCES_URL = '/vappio/terminateInstances_ws.py'

def loadCluster(host, clusterName, userName, timeout=30, tries=4):
    return http.performQuery(host,
                             CLUSTERINFO_URL,
                             dict(cluster=clusterName,
                                  user_name=userName),
                             timeout=timeout,
                             tries=tries)

def addInstances(host, clusterName, userName, numExec, numData, timeout=30, tries=4):
    return http.performQuery(host,
                             ADDINSTANCES_URL,
                             dict(cluster=clusterName,
                                  user_name=userName,
                                  num_exec=numExec,
                                  num_data=numData),
                             timeout=timeout,
                             tries=tries)

def terminateCluster(host, clusterName, userName, timeout=30, tries=4):
    return http.performQuery(host,
                             TERMINATECLUSTER_URL,
                             dict(cluster=clusterName,
                                  user_name=userName),
                             timeout=timeout,
                             tries=tries)    

def terminateInstances(host, clusterName, userName, byCriteria, criteriaValues, timeout=30, tries=4):
    return http.performQuery(host,
                             TERMINATEINSTANCES_URL,
                             dict(cluster=clusterName,
                                  user_name=userName,
                                  by_criteria=byCriteria,
                                  criteria_values=criteriaValues),
                             timeout=timeout,
                             tries=tries)

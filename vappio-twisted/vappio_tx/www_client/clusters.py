from igs_tx.utils import http

ADDINSTANCES_URL = '/vappio/cluster_addinstances'
STARTCLUSTER_URL = '/vappio/cluster_start'
TERMINATECLUSTER_URL = '/vappio/cluster_terminate'
TERMINATEINSTANCES_URL = '/vappio/cluster_terminateinstances'
LISTCLUSTERS_URL = '/vappio/cluster_list'


def listClusters(host, criteria, userName, authToken=None, timeout=30, tries=4):
    options = {}
    if authToken:
        options['auth_token'] = authToken
        
    return http.performQuery(host,
                             LISTCLUSTERS_URL,
                             dict(criteria=criteria,
                                  user_name=userName,
                                  options=options),
                             timeout=timeout,
                             tries=tries)

def addInstances(host, clusterName, userName, numExec, numData, timeout=30, tries=4):
    return http.performQuery(host,
                             ADDINSTANCES_URL,
                             dict(cluster_name=clusterName,
                                  user_name=userName,
                                  num_exec=numExec,
                                  num_data=numData),
                             timeout=timeout,
                             tries=tries)

def startCluster(host,
                 clusterName,
                 userName,
                 numExec,
                 numData,
                 credName,
                 conf,
                 timeout=30,
                 tries=4):
    return http.performQuery(host,
                             STARTCLUSTER_URL,
                             dict(cluster_name=clusterName,
                                  user_name=userName,
                                  num_exec=numExec,
                                  num_data=numData,
                                  cred_name=credName,
                                  conf=conf),
                             timeout=timeout,
                             tries=tries)    

def terminateCluster(host,
                     clusterName,
                     userName,
                     authToken,
                     timeout=30,
                     tries=4):
    return http.performQuery(host,
                             TERMINATECLUSTER_URL,
                             dict(cluster_name=clusterName,
                                  user_name=userName,
                                  auth_token=authToken),
                             timeout=timeout,
                             tries=tries)    

def terminateInstances(host, clusterName, userName, byCriteria, criteriaValues, timeout=30, tries=4):
    return http.performQuery(host,
                             TERMINATEINSTANCES_URL,
                             dict(cluster_name=clusterName,
                                  user_name=userName,
                                  by_criteria=byCriteria,
                                  criteria_values=criteriaValues),
                             timeout=timeout,
                             tries=tries)

##
# This is the webservice calls for dealing with the cluster

from igs.cgi.request import performQuery

ADDINSTANCES_URL = '/vappio/cluster_addinstances'
STARTCLUSTER_URL = '/vappio/cluster_start'
TERMINATECLUSTER_URL = '/vappio/cluster_terminate'
TERMINATEINSTANCES_URL = '/vappio/cluster_terminateinstances'
LISTCLUSTERS_URL = '/vappio/cluster_list'


def startCluster(host, cluster, num_exec, num_data, cred, conf):
    """
    Start a cluster
    """
    return performQuery(host, STARTCLUSTER_URL, dict(cluster_name=cluster,
                                                     num_exec=num_exec,
                                                     num_data=num_data,
                                                     cred_name=cred,
                                                     conf=conf))

def addInstances(host, name, numExec, numData):
    """
    Add instance to a cluster

    updateDirs is being deprecated
    """
    return performQuery(host, ADDINSTANCES_URL, dict(cluster_name=name,
                                                     num_exec=numExec,
                                                     num_data=numData))

def terminateCluster(host, cluster):
    return performQuery(host, TERMINATECLUSTER_URL, dict(cluster_name=cluster))
    
def terminateInstances(host, cluster, byCriteria, criteriaValues):
    return performQuery(host, TERMINATEINSTANCES_URL, dict(cluster_name=cluster,
                                                           by_criteria=byCriteria,
                                                           criteria_values=criteriaValues))


def listClusters(host, criteria={}):
    """
    Return a list of existing cluters
    """
    return performQuery(host, LISTCLUSTERS_URL, dict(criteria=criteria))

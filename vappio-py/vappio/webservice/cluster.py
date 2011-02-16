##
# This is the webservice calls for dealing with the cluster

from igs.cgi.request import performQuery


STARTCLUSTER_URL = '/vappio/startCluster_ws.py'
CLUSTERINFO_URL = '/vappio/clusterInfo_ws.py'
ADDINSTANCES_URL = '/vappio/addInstances_ws.py'
TERMINATECLUSTER_URL = '/vappio/terminateCluster_ws.py'
TERMINATEINSTANCES_URL = '/vappio/terminateInstances_ws.py'
LISTCLUSTERS_URL = '/vappio/listClusters_ws.py'


def startCluster(host, cluster, num_exec, num_data, cred, conf):
    """
    Start a cluster
    """
    return performQuery(host, STARTCLUSTER_URL, dict(cluster=cluster,
                                                     num_exec=num_exec,
                                                     num_data=num_data,
                                                     cred_name=cred,
                                                     conf=conf))

def loadCluster(host, name):
    """
    Loads cluster information

    Loading cluster information can involve talking to other hosts.
    Some of those hosts may fail to respond, in that case partial means
    that it is ok if loadCluster returns only what it can load.  Otherwise
    it will fail out completely
    """
    return performQuery(host, CLUSTERINFO_URL, dict(cluster=name))



def addInstances(host, name, numExec, numData):
    """
    Add instance to a cluster

    updateDirs is being deprecated
    """
    return performQuery(host, ADDINSTANCES_URL, dict(cluster=name,
                                                     num_exec=numExec,
                                                     num_data=numData))

def terminateCluster(host, cluster):
    return performQuery(host, TERMINATECLUSTER_URL, dict(cluster=cluster))
    
def terminateInstances(host, cluster, byCriteria, criteriaValues):
    return performQuery(host, TERMINATEINSTANCES_URL, dict(cluster=cluster,
                                                           by_criteria=byCriteria,
                                                           criteria_values=criteriaValues))


def listClusters(host):
    """
    Return a list of existing cluters
    """
    return performQuery(host, LISTCLUSTERS_URL, dict(cluster='local'))

##
# This is the webservice calls for dealing with the cluster

from igs.cgi.request import performQuery

ADDINSTANCES_URL = '/vappio/cluster_addinstances'
STARTCLUSTER_URL = '/vappio/cluster_start'
IMPORTCLUSTER_URL = '/vappio/cluster_import'
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

def addInstances(host, name, numExec, numData, execType=None):
    """
    Add instance to a cluster

    updateDirs is being deprecated
    """
    return performQuery(host, ADDINSTANCES_URL, dict(cluster=name,
                                                     num_exec=numExec,
                                                     exec_instance_type=execType,
                                                     num_data=numData))

def terminateCluster(host, cluster):
    return performQuery(host, TERMINATECLUSTER_URL, dict(cluster_name=cluster))
    
def terminateInstances(host, cluster, byCriteria, criteriaValues):
    return performQuery(host, TERMINATEINSTANCES_URL, dict(cluster_name=cluster,
                                                           by_criteria=byCriteria,
                                                           criteria_values=criteriaValues))

def importCluster(host, srcCluster, dstCluster, cred):
    """
    Import a cluster from another CloVR  VM.

    """
    # This is a super shitty hack her
    if srcCluster == 'local':
        userName = ""
    else:
        userName = 'guest'

    # Do we want to have this hardcoded just to localhost?
    return performQuery('localhost', IMPORTCLUSTER_URL, dict(host=host,
                                                             src_cluster=srcCluster,
                                                             dst_cluster=dstCluster,
                                                             cred_name=cred,
                                                             user_name=userName))

def listClusters(host, criteria={}):
    """
    Return a list of existing cluters
    """
    return performQuery(host, LISTCLUSTERS_URL, dict(criteria=criteria))

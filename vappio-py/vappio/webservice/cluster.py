##
# This is the webservice calls for dealing with the cluster

from igs.cgi.request import performQuery

from vappio.cluster.control import clusterFromDict


STARTCLUSTER_URL = '/vappio/startCluster_ws.py'
CLUSTERINFO_URL = '/vappio/clusterInfo_ws.py'
ADDINSTANCES_URL = '/vappio/addInstances_ws.py'
TERMINATECLUSTER_URL = '/vappio/terminateCluster_ws.py'
LISTCLUSTERS_URL = '/vappio/listClusters_ws.py'

def startCluster(host, name, conf, num, ctype, updateDirs):
    """
    Start a cluster
    """
    return performQuery(host, STARTCLUSTER_URL, dict(name=name,
                                                     conf=conf,
                                                     num=num,
                                                     ctype=ctype,
                                                     update_dirs=updateDirs))

def loadCluster(host, name):
    """
    Loads cluster information
    """
    result = performQuery(host, CLUSTERINFO_URL, {'name': name})
    return clusterFromDict(result)


def addInstances(host, name, num, updateDirs):
    """
    Add instance to a cluster
    """
    cluster = loadCluster(host, name)
    return performQuery(cluster.master.publicDNS, ADDINSTANCES_URL, dict(num=num,
                                                                         update_dirs=updateDirs))

def terminateCluster(host, name):
    return performQuery(host, TERMINATECLUSTER_URL, dict(name=name))
    

def listClusters(host):
    """
    Return a list of existing cluters
    """
    return performQuery(host, LISTCLUSTERS_URL, dict())

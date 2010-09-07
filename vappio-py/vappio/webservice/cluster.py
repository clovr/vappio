##
# This is the webservice calls for dealing with the cluster

from igs.cgi.request import performQuery

from vappio.cluster.control import clusterFromDict


STARTCLUSTER_URL = '/vappio/startCluster_ws.py'
CLUSTERINFO_URL = '/vappio/clusterInfo_ws.py'
ADDINSTANCES_URL = '/vappio/addInstances_ws.py'
TERMINATECLUSTER_URL = '/vappio/terminateCluster_ws.py'
LISTCLUSTERS_URL = '/vappio/listClusters_ws.py'

def startCluster(host, name, conf, num, cred, updateDirs):
    """
    Start a cluster
    """
    return performQuery(host, STARTCLUSTER_URL, dict(name=name,
                                                     conf=conf,
                                                     num=num,
                                                     cred=cred,
                                                     update_dirs=updateDirs))

def loadCluster(host, name, partial=False):
    """
    Loads cluster information

    Loading cluster information can involve talking to other hosts.
    Some of those hosts may fail to respond, in that case partial means
    that it is ok if loadCluster returns only what it can load.  Otherwise
    it will fail out completely
    """
    result = performQuery(host, CLUSTERINFO_URL, dict(name=name,
                                                      partial=partial))
    return clusterFromDict(result)


def addInstances(host, name, num, updateDirs=False):
    """
    Add instance to a cluster

    updateDirs is being deprecated
    """
    cluster = loadCluster(host, name)
    return performQuery(cluster.master.publicDNS, ADDINSTANCES_URL, dict(num=num,
                                                                         update_dirs=updateDirs))

def terminateCluster(host, name, force):
    return performQuery(host, TERMINATECLUSTER_URL, dict(name=name,
                                                         force=force))
    

def listClusters(host):
    """
    Return a list of existing cluters
    """
    return performQuery(host, LISTCLUSTERS_URL, dict())

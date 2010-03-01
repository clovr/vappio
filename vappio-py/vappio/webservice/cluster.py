##
# This is the webservice calls for dealing with the cluster

from igs.cgi.request import performQuery

from vappio.cluster.control import clusterFromDict


STARTCLUSTER_URL = '/vappio/startCluster_ws.py'
CLUSTERINFO_URL = '/vappio/clusterInfo_ws.py'


def startCluster(host, name, conf, num, ctype, update_dirs):
    performQuery(host, STARTCLUSTER_URL, dict(name=name,
                                              conf=conf,
                                              num=num,
                                              ctype=ctype,
                                              update_dirs=update_dirs))

def loadCluster(host, name):
    """
    Loads cluster information
    """
    result = performQuery(host, CLUSTERINFO_URL, {'name': name})
    return clusterFromDict(result)


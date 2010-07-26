##
# Routines for managing cluster informatino in mongo
import json
import socket

import pymongo

from twisted.python.reflect import fullyQualifiedName, namedAny

from igs.utils.config import configFromMap
from igs.utils.functional import updateDict
from igs.utils.errors import TryError
from igs.cgi.request import performQuery

from vappio.cluster.control import Cluster, clusterToDict, clusterFromDict
from vappio.cluster.misc import getInstances

CLUSTERINFO_URL = '/vappio/clusterInfo_ws.py'

class ClusterDoesNotExist(Exception):
    pass


class ClusterLoadIncompleteError(Exception):
    def __init__(self, msg, cluster):
        self.msg = msg
        self.cluster = cluster

    def __str__(self):
        return str(self.msg)
    

def dump(cluster):
    """
    Dumps a cluster to MongoDB
    """

    clovr = pymongo.Connection().clovr
    clusters = clovr.clusters


    clusters.save(updateDict(clusterToDict(cluster),
                             dict(_id=cluster.name)))
    



def load(name):
    """
    Loads a cluster from MongoDB
    """

    clovr = pymongo.Connection().clovr
    clusters = clovr.clusters
    instances = clovr.instances
    
    cluster = clusters.find_one(dict(name=name))
    if not cluster:
        raise ClusterDoesNotExist(name)

    clust = clusterFromDict(cluster)

    
    if name != 'local' and clust.master.state == clust.ctype.Instance.RUNNING:
        try:
            result = performQuery(clust.master.publicDNS, CLUSTERINFO_URL, dict(name='local'), timeout=10)
            execNodes = [clust.ctype.instanceFromDict(i) for i in result['execNodes']]
            dataNodes = [clust.ctype.instanceFromDict(i) for i in result['dataNodes']]
            clust.addExecNodes(execNodes)
            clust.addDataNodes(dataNodes)
        except socket.timeout:
            raise ClusterLoadIncompleteError('Failed to contact master when loading cluster', clust)
    

    return clust

def cleanUp(name):
    """
    Removes a cluster and any record of it from the the colletion
    """
    clovr = pymongo.Connection().clovr
    clovr.clusters.remove(dict(name=name))
    

def listClusters():
    """
    Returns a list of clusters
    """
    return [c['name'] for c in pymongo.Connection().clovr.clusters.find()]

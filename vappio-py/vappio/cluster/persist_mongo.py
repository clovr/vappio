##
# Routines for managing cluster informatino in mongo
import json

import pymongo

from twisted.python.reflect import fullyQualifiedName, namedAny

from igs.utils.config import configFromMap
from igs.utils.functional import updateDict
from igs.cgi.request import performQuery

from vappio.cluster.control import Cluster
from vappio.cluster.misc import getInstances

CLUSTERINFO_URL = '/vappio/clusterInfo_ws.py'

class ClusterDoesNotExist(Exception):
    pass


def dump(cluster):
    """
    Dumps a cluster to MongoDB
    """

    clovr = pymongo.Connection().clovr
    clusters = clovr.clusters

    clusters.save(dict(_id=cluster.name,
                       name=cluster.name,
                       ctype=fullyQualifiedName(cluster.ctype),
                       master=cluster.ctype.instanceToDict(cluster.master),
                       config=json.dumps(dict([(k, cluster.config(k)) for k in cluster.config.keys()]))))

    instances = clovr.instances

    ##
    # Save exec and data nodes
    saveIds = [instances.save(updateDict(cluster.ctype.instanceToDict(i),
                                         dict(_id=i.instanceId,
                                              cluster=cluster.name,
                                              itype='execNode')))
               for i in cluster.execNodes]
    
    
    saveIds = [instances.save(updateDict(cluster.ctype.instanceToDict(i),
                                        dict(_id=i.instanceId,
                                             cluster=cluster.name,
                                             itype='dataNode')))
               for i in cluster.dataNodes]



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

    clust = Cluster(name, namedAny(cluster['ctype']), configFromMap(json.loads(cluster['config'])))

    mastInst = clust.ctype.instanceFromDict(cluster['master'])
    
    if name == 'local':
        execNodes = [clust.ctype.instanceFromDict(i) for i in instances.find(dict(cluster=name, itype='execNode'))]
        dataNodes = [clust.ctype.instanceFromDict(i) for i in instances.find(dict(cluster=name, itype='dataNode'))]
    elif mastInst.state == clust.ctype.Instance.RUNNING:
        result = performQuery(mastInst.publicDNS, CLUSTERINFO_URL, dict(name='local'))
        execNodes = [clust.ctype.instanceFromDict(i) for i in result['execNodes']]
        dataNodes = [clust.ctype.instanceFromDict(i) for i in result['dataNodes']]
    else:
        execNodes = []
        dataNodes = []
    
    clust.setMaster(mastInst)
    clust.addExecNodes(execNodes)
    clust.addDataNodes(dataNodes)

    return clust

def cleanUp(name):
    """
    Removes a cluster and any record of it from the the colletion
    """
    clovr = pymongo.Connection().clovr
    clovr.clusters.remove(dict(name=name))
    clovr.instances.remove(dict(cluster=name))
    

def listClusters():
    """
    Returns a list of clusters
    """
    return [c['name'] for c in pymongo.Connection().clovr.clusters.find()]

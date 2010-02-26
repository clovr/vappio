##
# Routines for managing cluster informatino in mongo
import json

import pymongo

from twisted.python.reflect import fullyQualifiedName, namedAny

from igs.utils.config import configFromMap

from vappio.cluster.control import Cluster
from vappio.cluster.misc import getInstances


CLUSTERINFO_URL = '/vappio/clusterInfo_ws.py'

class ClusterDoesNotExist(Exception):
    pass


def updateDict(d, nd):
    """
    Adds the key/values in nd to d and returns d
    """
    d.update(nd)
    return d

def dump(cluster):
    """
    Dumps a cluster to MongoDB
    """

    clovr = pymongo.Connection().clovr
    clusters = clovr.clusters

    clusters.insert(dict(_id=cluster.name,
                         name=cluster.name,
                         ctype=fullyQualifiedName(cluster.ctype),
                         master=cluster.ctype.instanceToDict(cluster.master),
                         config=json.dumps(dict([(k, cluster.config(k)) for k in cluster.config.keys()]))))

    instances = clovr.instances

    ##
    # Save exec and data nodes
    instances.insert([updateDict(cluster.ctype.instanceToDict(i),
                                 dict(_id=i.instanceId,
                                      cluster=cluster.name,
                                      itype='execNode'))
                      for i in cluster.execNodes])
    

    instances.insert([updateDict(cluster.ctype.instanceToDict(i),
                                 dict(_id=i.instanceId,
                                      cluster=cluster.name,
                                      itype='dataNode'))
                      for i in cluster.dataNodes])



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
    
    ##
    # Not right
    mastInst = clust.ctype.instanceFromDict(cluster['master'])
    
    if name == 'local':
        execNodes = [clust.ctype.instanceFromDict(i) for i in instances.find(dict(cluster=name, itype='execNode'))]
        dataNodes = [clust.ctype.instanceFromDict(i) for i in instances.find(dict(cluster=name, itype='dataNode'))]
    else:
        result = performQuery(mastInst.publicDNS, CLUSTERINFO_URL, {})
        execNodes = [clust.ctype.instanceFromDict(i) for i in result['execNodes']]
        dataNodes = [clust.ctype.instanceFromDict(i) for i in result['dataNodes']]
    
    clust.setMaster(mastInst)
    clust.addExecNodes(execNodes)
    clust.addDataNodes(dataNodes)

    return clust

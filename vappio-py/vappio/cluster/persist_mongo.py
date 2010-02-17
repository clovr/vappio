##
# Routines for managing cluster informatino in mongo
import json

import pymongo

from twisted.python.reflect import fullyQualifiedName, namedAny

from igs.utils.config import configFromMap

from vappio.cluster.control import Cluster
from vappio.cluster.misc import getInstances


class ClusterDoesNotExist(Exception):
    pass


def dump(cluster):
    """
    Dumps a cluster to MongoDB
    """

    clovr = pymongo.Connection().clovr
    clusters = clovr.clusters

    clusters.insert(dict(_id=cluster.name,
                         name=cluster.name,
                         ctype=fullyQualifiedName(cluster.ctype),
                         master=cluster.master.publicDNS,
                         config=json.dumps(dict([(k, cluster.config(k)) for k in cluster.config.keys()]))))

    instances = clovr.instances

    instances.insert([dict(_id=i.instanceId,
                           instanceId=i.instanceId,
                           publicDNS=i.publicDNS,
                           cluster=cluster.name,
                           itype='execNode')
                      for i in cluster.execNodes])

    instances.insert([dict(_id=i.instanceId,
                           instanceId=i.instanceId,
                           publicDNS=i.publicDNS,
                           cluster=cluster.name,
                           itype='dataNode')
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

    execNodes = [i['publicDNS'] for i in instances.find(dict(cluster=name, itype='execNode'))]
    dataNodes = [i['publicDNS'] for i in instances.find(dict(cluster=name, itype='dataNode'))]
    
    clust = Cluster(name, namedAny(cluster['ctype']), configFromMap(json.loads(cluster['config'])))

    clust.setMaster(getInstances(lambda i : i.publicDNS == cluster['master'], clust.ctype)[0])
    clust.addExecNodes(getInstances(lambda i : i.publicDNS in execNodes, clust.ctype))
    clust.addDataNodes(getInstances(lambda i : i.publicDNS in dataNodes, clust.ctype))

    return clust

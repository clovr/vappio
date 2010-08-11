##
# Routines for managing cluster informatino in mongo
import json

import pymongo

from twisted.python.reflect import fullyQualifiedName, namedAny

from igs.utils.config import configFromMap
from igs.utils.functional import updateDict
from igs.utils.errors import TryError
from igs.cgi.request import performQuery



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


    clusters.save(updateDict(cluster,
                             dict(_id=cluster['name'])))
    



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


    return cluster

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

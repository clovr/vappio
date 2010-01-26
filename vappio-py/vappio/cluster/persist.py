##
# API for persisting a cluster to disk.
# Right now this is a cheapo directory structure which looks like:
# $BASEDIR/$CLUSTER_NAME/[master, slaves, conf]

import os
import json

from twisted.python.reflect import fullyQualifiedName, namedAny

from igs.utils.config import configFromMap
from igs.utils.commands import runSystemEx

from vappio.cluster.control import Cluster
from vappio.cluster.misc import getInstances

class ClusterDoesNotExist(Exception):
    pass


def writeFile(fname, data):
    fout = open(fname, 'w')
    fout.write(data)
    fout.close()


def dump(baseDir, cluster):
    """
    Dumps the cluster information to directory structure
    """
    clusterDir = os.path.join(baseDir, 'cluster', cluster.name)
    if not os.path.exists(clusterDir):
        runSystemEx('mkdir -p ' + clusterDir)

    writeFile(os.path.join(clusterDir, 'master'), cluster.master.publicDNS)
    writeFile(os.path.join(clusterDir, 'slaves'), ((cluster.slaves or '') and
                                                   '\n'.join([s.publicDNS for s in cluster.slaves])))

    ##
    # let's let json serialize this for us
    writeFile(os.path.join(clusterDir, 'conf'), json.dumps(dict([(k, cluster.config(k)) for k in cluster.config.keys()])))
    writeFile(os.path.join(clusterDir, 'ctype'), fullyQualifiedName(cluster.ctype))
    

def load(baseDir, name):
    """
    Loads a cluster by name and returns a Cluster object
    """
    clusterDir = os.path.join(baseDir, 'cluster', name)
    if not os.path.exists(clusterDir):
        raise ClusterDoesNotExist()

    masterIp = open(os.path.join(clusterDir, 'master')).read().strip()
    slaveIps = [l.rstrip('\n') for l in open(os.path.join(clusterDir, 'slaves')).readlines()]
    conf = configFromMap(json.loads(open(os.path.join(clusterDir, 'conf')).read()))
    ctype = namedAny(open(os.path.join(clusterDir, 'ctype')).read().strip())

    instances = getInstances(lambda i : i.publicDNS == masterIp, ctype)
    if not instances:
        raise ClusterDoesNotExist('Master instances is not up: %r' % masterIp)

    mastInst = instances[0]

    instances = getInstances(lambda i : i.publicDNS in slaveIps, ctype)

    slaves = instances
    
    cluster = Cluster(name, ctype, conf)
    cluster.setMaster(mastInst)
    cluster.addExecs(slaves)

    return cluster

def cleanup(baseDir, name):
    clusterDir = os.path.join(baseDir, 'cluster', name)
    runSystemEx('rm -rf ' + clusterDir)
    

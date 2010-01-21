##
# API for persisting a cluster to disk.
# Right now this is a cheapo directory structure which looks like:
# $BASEDIR/$CLUSTER_NAME/[master, slaves, conf]

import os

from twisted.python.reflect import qual, namedAny

from igs.utils.config import configFromStream

from vappio.cluster.control import Cluster
from vappio.cluster.misc import getInstances

class ClusterDoesNotExist(Exception):
    pass


def typeToStr(s):
    """
    If something is a list converts it to a ',' seperated string
    Also removes '\n' to ' '
    """
    if hasattr(s, 'extend'):
        s = ','.join([str(i) for i in s])
    if hasattr(s, 'replace'):
        s = s.replace('\n', ' ')

    return s

def writeFile(fname, data):
    fout = open(fname, 'w')
    fout.write(data)
    fout.close()


def dump(baseDir, cluster):
    """
    Dumps the cluster information to directory structure
    """
    if not os.path.exists(baseDir):
        os.mkdir(baseDir)
        
    clusterDir = os.path.join(baseDir, cluster.name)
    if not os.path.exists(clusterDir):
        os.mkdir(clusterDir)

    writeFile(os.path.join(clusterDir, 'master'), cluster.master.publicDNS)
    writeFile(os.path.join(clusterDir, 'slaves'), ((cluster.slaves or '') and
                                                   '\n'.join([s.publicDNS for s in cluster.slaves])))
    writeFile(os.path.join(clusterDir, 'conf'), ('[]\n' +
                                                 '\n'.join(['%s=%s' % (k, str(typeToStr(cluster.config(k)))) for k in cluster.config.keys()])))
    #writeFile(os.path.join(clusterDir, 'ctype'), qual(cluster.ctype))
    writeFile(os.path.join(clusterDir, 'ctype'), 'vappio.ec2.control')


def load(baseDir, name):
    """
    Loads a cluster by name and returns a Cluster object
    """
    clusterDir = os.path.join(baseDir, name)
    if not os.path.exists(clusterDir):
        raise ClusterDoesNotExist()

    masterIp = open(os.path.join(clusterDir, 'master')).read().strip()
    slaveIps = [l.rstrip('\n') for l in open(os.path.join(clusterDir, 'slaves')).readlines()]
    conf = configFromStream(open(os.path.join(clusterDir, 'conf')))
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

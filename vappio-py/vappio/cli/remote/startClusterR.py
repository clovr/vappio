#!/usr/bin/env python
##
# This adds instances to the current cluster.  This should run on the master node of
# whatever cluster instances are being added to
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone, restrictValues
from igs.utils.config import configFromEnv, configFromStream, configFromMap
from igs.utils.logging import logPrint, errorPrint, debugPrint
from igs.utils.functional import compose
from igs.utils.commands import runSingleProgramEx
from igs.utils.errors import TryError

from vappio.core.error_handler import runCatchError, mongoFail

from vappio.cluster.control import Cluster, startMaster
from vappio.cluster.persist_mongo import dump

from vappio.webservice.cluster import addInstances

from vappio.ec2 import control as ec2control

OPTIONS = [
    ('conf', '', '--conf', 'Name of config file to use', compose(lambda x : '${env.VAPPIO_HOME}/vappio-conf/' + x, notNone)),
    ('name', '', '--name', 'Name of the cluster', notNone),
    ('ctype', '', '--ctype', 'Type of cluster to start', compose(restrictValues(['ec2', 'nimbus']), notNone)),
    ('num', '', '--num', 'Number of nodes to create', compose(int, notNone)),
    ('update_dirs', '', '--update_dirs', 'Update scritps directories', defaultIfNone(False), True),
    ]

def updateCluster(cluster, mastL):
    """
    This keeps on setting the cluster master to the new value and
    dumping it to the database
    """
    master = mastL[0]
    debugPrint(lambda : 'Updating cluster: %s %s' % (master.publicDNS, master.state))
    cluster.setMaster(master)
    dump(cluster)
    

def main(options, _args):
    options = configFromMap(
        {'cluster': {'master_groups': [f.strip() for f in options('cluster.master_groups').split(',')],
                     'exec_groups': [f.strip() for f in options('cluster.exec_groups').split(',')],
                     }
         }, options)
    ctype = ec2control
    
    cl = Cluster(options('general.name'), ctype, options)
    try:
        startMaster(cl, lambda m : updateCluster(cl, m), devMode=False, releaseCut=False)
        if options('general.num'):
            addInstances('localhost', options('general.name'), options('general.num'), options('general.update_dirs'))
    except TryError, err:
        if cl.master:
            cl.master.state = 'Error'
        errorPrint('There was an error bringing up the cluster: ' + str(err.msg))
        
    dump(cl)


    
if __name__ == '__main__':
    runCatchError(lambda : main(*buildConfigN(OPTIONS)),
                  mongoFail(dict(action='startCluster')))

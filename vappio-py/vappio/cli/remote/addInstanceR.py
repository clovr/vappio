#!/usr/bin/env python
##
# This adds instances to the current cluster.  This should run on the master node of
# whatever cluster instances are being added to

import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.config import configFromEnv, configFromStream, configFromMap
from igs.utils.logging import logPrint
from igs.utils.functional import compose
from igs.utils.commands import runSingleProgramEx

from vappio.cluster.misc import getInstances
from vappio.cluster.control import Cluster, startExecNodes
from vappio.cluster.persist import load, dump, ClusterDoesNotExist

from vappio.ec2 import control as ec2control

OPTIONS = [
    ('num', '', '--num', 'Number of nodes to create', compose(int, notNone)),
    ('update_dirs', '', '--update_dirs', 'Update scritps directories', defaultIfNone(False), True),
    ]

def main(options, _args):
    try:
        cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), 'local')
    except ClusterDoesNotExist:
        options = configFromMap({'general': {'ctype': 'ec2'}},
                                configFromStream(open('/tmp/machine.conf'),
                                                 configFromEnv()))
        options = configFromMap(
            {'cluster': {'master_groups': [f.strip() for f in options('cluster.master_groups').split(',')],
                         'exec_groups': [f.strip() for f in options('cluster.exec_groups').split(',')]
                         }
             }, options)
        cluster = Cluster('local', ec2control, options)
        cluster.setMaster(getInstances(lambda i : i.privateDNS == cluster.config('MASTER_IP'), ec2control)[0])

    startExecNodes(cluster, options('general.num'))
    
    dump(os.path.join(options('env.VAPPIO_HOME'), 'db'), cluster)

    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

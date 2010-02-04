#!/usr/bin/env python
##
# This adds instances to the current cluster.  This should run on the master node of
# whatever cluster instances are being added to

import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.config import configFromMap
from igs.utils.logging import logPrint
from igs.utils.functional import compose

from vappio.cluster.persist import load, dump, ClusterDoesNotExist

from vappio.ec2 import ec2control

def main(options, _args):
    try:
        cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), 'local')
    except ClusterDoesNotExist:
        cluster = Cluster('local', ec2control, configFromStream('/tmp/machine.conf'))
    
    startExecNodes(cluster, options('general.num'))
    
    dump(os.path.join(options('env.VAPPIO_HOME'), 'db'), cluster)

    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

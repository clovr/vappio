#!/usr/bin/env python

import os

from igs.utils.cli import MissingOptionError, buildConfigN, notNone, defaultIfNone
from igs.utils.config import configFromMap
from igs.utils.logging import logPrint

from vappio.cluster.persist import load, dump, cleanup
from vappio.cluster.misc import getInstances
from vappio.cluster.control import terminateCluster

OPTIONS = [
    ('name', '', '--name', 'Name of cluster', notNone),
    ]


URL = '/vappio/clusterInfo_ws.py'

def main(options, _args):
    cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))

    terminateCluster(cluster)

    cleanup(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))
    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

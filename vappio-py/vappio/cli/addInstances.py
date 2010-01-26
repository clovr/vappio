#!/usr/bin/env python

import os

from igs.utils.cli import MissingOptionError, buildConfigN, notNone, defaultIfNone
from igs.utils.config import configFromMap
from igs.utils.logging import logPrint

from vappio.cluster.persist import load, dump


OPTIONS = [
    ('name', '', '--name', 'Name of cluster (in this case public host name of master)', notNone),
    ('num', '', '--num', 'Number of nodes to create', int),
    ('update_dirs', '', '--update_dirs', 'Update scritps directories', defaultIfNone(False), True),
    ]


def main(options, _args):
    cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))
    
    cluster.createExecs(options('general.num'), False)
    
    dump(os.path.join(options('env.VAPPIO_HOME'), 'db'), cluster)

    logPrint('The master IP is: ' + cluster.master.publicDNS)

    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

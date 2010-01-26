#!/usr/bin/env python

import os

from igs.utils.cli import MissingOptionError, buildConfigN, notNone, defaultIfNone
from igs.utils.config import configFromMap
from igs.utils.logging import logPrint

from vappio.cluster.persist import load, dump, cleanup


OPTIONS = [
    ('name', '', '--name', 'Name of cluster', notNone),
    ]


def main(options, _args):
    cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))
    
    cluster.terminateCluster()

    cleanup(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))
    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

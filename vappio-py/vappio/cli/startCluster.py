#!/usr/bin/env python

import os

from igs.utils.cli import buildConfigN, notNone, restrictValues
from igs.utils.config import configFromMap, configFromStream
from igs.utils.logging import logPrint
from igs.utils.functional import identity, compose

from vappio.cluster.control import Cluster
from vappio.cluster.persist import dump
from vappio.ec2 import control as ec2Control


OPTIONS = [
    ('conf', '', '--conf', 'Config file name', notNone),
    ('name', '', '--name', 'Name of cluster', notNone),
    ('num', '', '--num', 'Number of exec nodes to start', int),
    ('ctype', '', '--ctype', 'Type of cluster', compose(restrictValues(['ec2', 'nimbus']), notNone)),
    ('dev_mode', '-d', '--dev_mode', 'Dev mode or not', identity, True),
    ('release_cut', '', '--release_cut', 'Want to cut a release', identity, True),
    ('update_dirs', '', '--update_dirs', 'Want to update scripts dirs once instance is up', identity, True),
    ]


def main(options, _args):
    options = configFromMap(
        {'cluster': {'master_groups': [f.strip() for f in options('cluster.master_groups').split(',')],
                     'exec_groups': [f.strip() for f in options('cluster.exec_groups').split(',')]
                     }
         }, options)
    ctype = ec2Control
    cl = Cluster(options('general.name'), ctype, options)
    cl.startCluster(options('general.num'), devMode=options('general.dev_mode'), releaseCut=options('general.release_cut'))
    dump(os.path.join(options('env.VAPPIO_HOME'), 'db'), cl)
    logPrint('The master IP is: ' + cl.master.publicDNS)

    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

#!/usr/bin/env python
import os

from igs.utils.cli import buildConfigN, notNone, restrictValues
from igs.utils.config import configFromMap, configFromStream
from igs.utils.logging import logPrint, errorPrint
from igs.utils.functional import identity, compose

from vappio.cluster.control import Cluster, startMaster, TryError
from vappio.cluster.persist import dump

from vappio.ec2 import control as ec2Control

from vappio.cli import addInstances


OPTIONS = [
    ('conf', '', '--conf', 'Config file name', notNone),
    ('name', '', '--name', 'Name of cluster', notNone),
    ('num', '', '--num', 'Number of exec nodes to start', int),
    ('ctype', '', '--ctype', 'Type of cluster', compose(restrictValues(['ec2', 'nimbus']), notNone)),
    ('dev_mode', '-d', '--dev_mode', 'Dev mode or not', identity, True),
    ('release_cut', '', '--release_cut', 'Want to cut a release', identity, True),
    ('update_dirs', '', '--update_dirs', 'Want to update scripts dirs once instance is up', identity, True),
    ]


def main(options, args):
    options = configFromMap(
        {'cluster': {'master_groups': [f.strip() for f in options('cluster.master_groups').split(',')],
                     'exec_groups': [f.strip() for f in options('cluster.exec_groups').split(',')]
                     }
         }, options)
    ctype = ec2Control
    cl = Cluster(options('general.name'), ctype, options)
    try:
        startMaster(cl, options('general.num'), devMode=options('general.dev_mode'), releaseCut=options('general.release_cut'))
    except TryError, err:
        errorPrint('There was an error bringing up the cluster: ' + str(err.msg))
        
    dump(os.path.join(options('env.VAPPIO_HOME'), 'db'), cl)

    ##
    # A bit nasty, until addInstances gets moved into a library
    addInstances.main(options, args)
    logPrint('The master IP is: ' + cl.master.publicDNS)

    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

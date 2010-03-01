#!/usr/bin/env python
import sys
import time

from igs.utils.cli import buildConfigN, notNone, restrictValues, defaultIfNone
from igs.utils.config import configFromMap, configFromStream
from igs.utils.logging import logPrint, errorPrint
from igs.utils.functional import identity, compose

from vappio.webservice.cluster import startCluster, loadCluster



OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),
    ('conf_name', '', '--conf-name', 'Config name', notNone),
    ('name', '', '--name', 'Name of cluster', notNone),
    ('num', '', '--num', 'Number of exec nodes to start', int),
    ('ctype', '', '--ctype', 'Type of cluster', compose(restrictValues(['ec2', 'nimbus']), notNone)),
    ('block', '', '--block', 'Block until cluster is up', identity, True),
    ('dev_mode', '-d', '--dev_mode', 'Dev mode or not', identity, True),
    ('release_cut', '', '--release_cut', 'Want to cut a release', identity, True),
    ('update_dirs', '', '--update_dirs', 'Want to update scripts dirs once instance is up', identity, True),
    ]


URL = '/vappio/startCluster_ws.py'

def main(options, args):
    startCluster(options('general.host'),
                 options('general.name'),
                 options('general.conf_name'),
                 options('general.num'),
                 options('general.ctype'),
                 options('general.update_dirs'))

    if options('general.block'):
        time.sleep(30)
        cluster = loadCluster(options('general.host'), options('general.name'))
        while cluster.master.state != cluster.ctype.Instance.RUNNING:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(30)
            cluster = loadCluster(options('general.host'), options('general.name'))

        print
    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

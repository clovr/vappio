#!/usr/bin/env python
import sys
import time

from igs.utils.cli import buildConfigN, notNone, restrictValues, defaultIfNone
from igs.utils.config import configFromMap, configFromStream
from igs.utils.logging import logPrint, errorPrint, debugPrint
from igs.utils.functional import identity, compose, tryUntil

from vappio.webservice.cluster import startCluster, loadCluster
from vappio.webservice.task import loadTask

from vappio.tasks.task import TASK_FAILED
from vappio.tasks.utils import blockOnTask

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),
    ('conf_name', '', '--conf-name', 'Config name, defaults to clovr.conf', defaultIfNone('clovr.conf')),
    ('name', '', '--name', 'Name of cluster', notNone),
    ('num', '', '--num', 'Number of exec nodes to start', int),
    ('ctype', '', '--ctype', 'Type of cluster', compose(restrictValues(['ec2', 'nimbus']), notNone)),
    ('block', '-b', '--block', 'Block until cluster is up', identity, True),
    ('dev_mode', '-d', '--dev_mode', 'Dev mode or not', identity, True),
    ('release_cut', '', '--release_cut', 'Want to cut a release', identity, True),
    ('update_dirs', '', '--update_dirs', 'Want to update scripts dirs once instance is up', identity, True),
    ]


        


def main(options, args):
    taskName = startCluster(options('general.host'),
                            options('general.name'),
                            options('general.conf_name'),
                            options('general.num'),
                            options('general.ctype'),
                            options('general.update_dirs'))

    if options('general.block'):
        state = blockOnTask('localhost', 'local', taskName)
        if state == TASK_FAILED:
            raise Exception('Starting cluster failed')
    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

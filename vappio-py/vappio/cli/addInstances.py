#!/usr/bin/env python
import sys
import time

from igs.utils.cli import MissingOptionError, buildConfigN, notNone, defaultIfNone
from igs.utils.logging import logPrint, errorPrint, debugPrint
from igs.utils.functional import compose, identity, tryUntil

from vappio.webservice.cluster import addInstances, loadCluster

from vappio.tasks.task import TASK_FAILED
from vappio.tasks.utils import blockOnTask


OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),    
    ('name', '', '--name', 'Name of cluster (in this case public host name of master)', notNone),
    ('num', '', '--num', 'Number of nodes to create', compose(int, notNone)),
    ('block', '-b', '--block', 'Block until cluster is up', identity, True),
    ('update_dirs', '', '--update_dirs', 'Update scritps directories', defaultIfNone(False), True),
    ]

def main(options, _args):
    if options('general.name') == 'local':
        raise Exception('Cannot add instance to local cluster')

    taskName = addInstances(options('general.host'),
                 options('general.name'),
                 options('general.num'),
                 options('general.update_dirs'))
    
    logPrint('Launching %d instances' % options('general.num'))

    if options('general.block'):
    if options('general.block'):
        state = blockOnTask('localhost', 'local', taskName)
        if state == TASK_FAILED:
            raise Exception('Starting cluster failed')
        
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

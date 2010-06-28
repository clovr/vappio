#!/usr/bin/env python
from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.functional import compose, identity
from igs.utils.logging import logPrint

from vappio.webservice.cluster import addInstances

from vappio.tasks.task import TASK_FAILED
from vappio.tasks.utils import blockOnTask


OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),    
    ('name', '', '--name', 'Name of cluster (in this case public host name of master)', notNone),
    ('num', '', '--num', 'Number of nodes to create', compose(int, notNone)),
    ('block', '-b', '--block', 'Block until cluster is up', identity, True),
    ('update_dirs', '', '--update-dirs', 'Update scripts directories', defaultIfNone(False), True),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end', defaultIfNone(False), True),
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
        state = blockOnTask(options('general.host'), options('general.name'), taskName)
        if state == TASK_FAILED:
            raise Exception('Starting cluster failed')

    if options('general.print_task_name'):
        print taskName
        
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

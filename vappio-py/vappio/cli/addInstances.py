#!/usr/bin/env python
from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.functional import compose, identity

from vappio.webservice.cluster import addInstances

from vappio.tasks.utils import runTaskStatus


OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),    
    ('name', '', '--name', 'Name of cluster (in this case public host name of master)', defaultIfNone('local')),
    ('num_exec', '', '--num-exec', 'Number of exec nodes to create', compose(int, notNone)),
    ('block', '-b', '--block', 'Block until cluster is up', identity, True),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end', defaultIfNone(False), True),
    ]

def main(options, _args):
    if options('general.name') == 'local':
        raise Exception('Cannot add instance to local cluster')

    taskName = addInstances(options('general.host'),
                            options('general.name'),
                            options('general.num_exec'),
                            0)
    
    if options('general.print_task_name'):
        print taskName
    else:
        runTaskStatus(taskName, clusterName=options('general.name'))


        
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

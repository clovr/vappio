#!/usr/bin/env python
from igs.utils.cli import buildConfigN, notNone, defaultIfNone

from vappio.webservice.cluster import terminateCluster

from vappio.tasks.utils import runTaskStatus

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),
    ('cluster', '', '--cluster', 'Name of cluster', notNone),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end', defaultIfNone(False), True),    
    ]


def main(options, _args):
    taskName = terminateCluster(options('general.host'), options('general.cluster'))

    if options('general.print_task_name'):
        print taskName
    else:
        runTaskStatus(taskName, clusterName='local')
    
    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

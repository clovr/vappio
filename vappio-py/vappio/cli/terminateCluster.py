#!/usr/bin/env python
from igs.utils.cli import buildConfigN, notNone, defaultIfNone

from vappio.webservice.cluster import terminateCluster

from vappio.tasks.utils import runTaskStatus

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', notNone),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end', defaultIfNone(False), True),    
    ]


URL = '/vappio/clusterInfo_ws.py'

def main(options, _args):
    if options('general.name') == 'local':
        raise Exception('Cannot terminate local cluster')
    
    taskName = terminateCluster(options('general.host'), options('general.name'))

    if options('general.print_task_name'):
        print taskName
    else:
        runTaskStatus(taskName, clusterName='local')
    
    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

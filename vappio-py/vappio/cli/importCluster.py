#!/usr/bin/env python

from igs.utils import cli

from vappio.webservice.cluster import importCluster

from vappio.tasks.utils import runTaskStatus

OPTIONS = [
    ('host', '', '--host', 'Host from which cluster will be imported', cli.notNone),
    ('src_cluster', '', '--src-cluster', 'Name of remote cluster to import', cli.defaultIfNone('local')),
    ('dst_cluster', '', '--dst-cluster', 'Name of cluster on importing VM', cli.notNone),
    ('cred', '', '--cred', 'Credential to use', cli.notNone),
    ('print_task_name', 
     '-t', 
     '--print-task-name',
     'Print name of the task at the end',
     cli.defaultIfNone(False),
     cli.BINARY),
    ]

def main(options, _args):
    taskName = importCluster(options('general.host'),
                             options('general.src_cluster'),
                             options('general.dst_cluster'),
                             options('general.cred'))


    if options('general.print_task_name'):
        print taskName
    else:
        runTaskStatus(taskName)

    
if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))


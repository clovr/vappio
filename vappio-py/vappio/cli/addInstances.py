#!/usr/bin/env python
from igs.utils import cli
from igs.utils.functional as func

from vappio.webservice.cluster import addInstances

from vappio.tasks.utils import runTaskStatus


OPTIONS = [
    ('host',
     '',
     '--host',
     'Host of webservice to contact',
     cli.defaultIfNone('localhost')),    
    ('cluster',
     '',
     '--cluster',
     'Name of cluster (in this case public host name of master)',
     cli.defaultIfNone('local')),
    ('num_exec',
     '',
     '--num-exec',
     'Number of exec nodes to create',
     func.compose(int, notNone)),
    ('exec_type',
     '',
     '--type',
     'Specify a type for exec if you want',
     func.identity)
    ('block',
     '-b',
     '--block',
     'Block until cluster is up',
     func.identity,
     cli.BINARY),
    ('print_task_name',
     '-t',
     '--print-task-name',
     'Print the name of the task at the end',
     cli.defaultIfNone(False),
     cli.BINARY),
    ]

def main(options, _args):
    taskName = addInstances(options('general.host'),
                            options('general.cluster'),
                            options('general.num_exec'),
                            options('general.exec_type'),
                            0)
    
    if options('general.print_task_name'):
        print taskName
    else:
        runTaskStatus(taskName, clusterName=options('general.cluster'))


        
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

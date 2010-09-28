#!/usr/bin/env python
from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.functional import identity

from vappio.webservice.cluster import startCluster

from vappio.tasks.utils import runTaskStatus

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),
    ('conf_name', '', '--conf-name', 'Config name, defaults to clovr.conf', defaultIfNone('clovr.conf')),
    ('name', '', '--name', 'Name of cluster', notNone),
    ('num', '', '--num', 'Number of exec nodes to start', int),
    ('cred', '', '--cred', 'Credential to use', notNone),
    ('block', '-b', '--block', 'Block until cluster is up', identity, True),
    ('update_dirs', '', '--update_dirs', 'Want to update scripts dirs once instance is up', identity, True),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end', defaultIfNone(False), True),
    ]

def main(options, _args):
    ##
    # Just do nothing if ctype is local or name is local
    if options('general.cred') != 'local' and options('general.name') != 'local':
        taskName = startCluster(options('general.host'),
                                options('general.name'),
                                options('general.conf_name'),
                                options('general.num'),
                                options('general.cred'),
                                options('general.update_dirs'))


        if options('general.print_task_name'):
            print taskName
        else:
            runTaskStatus(taskName)

    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

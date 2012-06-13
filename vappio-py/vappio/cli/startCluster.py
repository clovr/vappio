#!/usr/bin/env python
from igs.utils import cli
from igs.utils import functional as func

from vappio.webservice.cluster import startCluster

from vappio.tasks.utils import runTaskStatus

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', cli.defaultIfNone('localhost')),
    ('cluster', '', '--cluster', 'Name of cluster', cli.notNone),
    ('num_exec', '', '--num-exec', 'Number of exec nodes to start', int),
    ('cred', '', '--cred', 'Credential to use', cli.notNone),
    ('master_instance_type',
     '',
     '--master-instance-type',
     'Which instance type to use, defaults to "default"',
     cli.defaultIfNone('default')),
    ('exec_instance_type',
     '',
     '--exec-instance-type',
     'Which instance type to use, defaults to "default"',
     cli.defaultIfNone('default')),    
    ('master_bid_price',
     '',
     '--master-bid-price',
     'Bid price for master, defaults to nothing (on demand instance)',
     cli.defaultIfNone('')),
    ('exec_bid_price',
     '',
     '--exec-bid-price',
     'Bid price for exec nodes, defaults to nothing (on demand instance)',
     cli.defaultIfNone('')),
    ('config_options', '-c', '--config',
     'Specify arbitrary values to replace in the cluster config. Can specify multiple i.e. -c foo.Bar=foo -c cluster.BAZ=baz',
     cli.defaultIfNone([]), cli.LIST),
    ('print_task_name',
     '-t',
     '--print-task-name',
     'Print the name of the task at the end',
     cli.defaultIfNone(False),
     cli.BINARY),
    ]

def main(options, _args):
    conf = func.updateDict(dict([c.split('=') for c in options('general.config_options')]),
                           {'cluster.master_type': options('general.master_instance_type'),
                            'cluster.exec_type': options('general.exec_instance_type'),
                            'cluster.master_bid_price': options('general.master_bid_price'),
                            'cluster.exec_bid_price': options('general.exec_bid_price')})

    
    taskName = startCluster(options('general.host'),
                            options('general.cluster'),
                            options('general.num_exec'),
                            0,
                            options('general.cred'),
                            conf)


    if options('general.print_task_name'):
        print taskName
    else:
        runTaskStatus(taskName)

    
if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))

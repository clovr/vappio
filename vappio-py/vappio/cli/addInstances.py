#!/usr/bin/env python

import os

from igs.utils.cli import MissingOptionError, buildConfigN, notNone, defaultIfNone
from igs.utils.logging import logPrint, errorPrint
from igs.utils.functional import compose
from igs.cgi.request import performQuery

from vappio.webservice.cluster import addInstances

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),    
    ('name', '', '--name', 'Name of cluster (in this case public host name of master)', notNone),
    ('num', '', '--num', 'Number of nodes to create', compose(int, notNone)),
    ('block', '', '--block', 'Block until cluster is up', identity, True),
    ('update_dirs', '', '--update_dirs', 'Update scritps directories', defaultIfNone(False), True),
    ]


def main(options, _args):
    if options('general.name') == 'local':
        raise Exception('Cannot add instance to local cluster')

    addInstances(options('general.host'),
                 options('general.name'),
                 options('general.num'),
                 options('general.update_dirs'))
    
    logPrint('Launching %d instances' % options('general.num'))

    if options('general.block'):
        time.sleep(30)
        cluster = loadCluster(options('general.host'), options('general.name'))
        while any([i.state != cluster.ctype.Instance.RUNNING
                   for i in cluster.execNodes + cluster.dataNodes]):
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(30)
            cluster = loadCluster(options('general.host'), options('general.name'))

        print
        
    
        
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

#!/usr/bin/env python
import sys
import time

from igs.utils.cli import MissingOptionError, buildConfigN, notNone, defaultIfNone
from igs.utils.logging import logPrint, errorPrint, debugPrint
from igs.utils.functional import compose, identity, tryUntil

from vappio.webservice.cluster import addInstances, loadCluster

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),    
    ('name', '', '--name', 'Name of cluster (in this case public host name of master)', notNone),
    ('num', '', '--num', 'Number of nodes to create', compose(int, notNone)),
    ('block', '-b', '--block', 'Block until cluster is up', identity, True),
    ('update_dirs', '', '--update_dirs', 'Update scritps directories', defaultIfNone(False), True),
    ]


def testClusterUp(options):
    def _():
        try:
            cluster = loadCluster(options('general.host'), options('general.name'))
            return all([i.state == cluster.ctype.Instance.RUNNING
                        for i in cluster.execNodes + cluster.dataNodes])
        except Exception, err:
            debugPrint(lambda : 'Unknown error checking master state: ' + str(err))

    return _
        

def progress():
    sys.stdout.write('.')
    sys.stdout.flush()
    time.sleep(30)




def main(options, _args):
    if options('general.name') == 'local':
        raise Exception('Cannot add instance to local cluster')

    addInstances(options('general.host'),
                 options('general.name'),
                 options('general.num'),
                 options('general.update_dirs'))
    
    logPrint('Launching %d instances' % options('general.num'))

    if options('general.block'):
        tryUntil(30, progress, testClusterUp(options))
        print
        
    
        
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

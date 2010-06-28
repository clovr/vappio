#!/usr/bin/env python
from igs.utils.cli import buildConfigN, notNone, defaultIfNone

from vappio.webservice.cluster import terminateCluster

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', notNone),
    ('force', '-f', '--force', 'Force cluster to shut down and be cleaned up, use with caution!', defaultIfNone(False), True)
    ]


URL = '/vappio/clusterInfo_ws.py'

def main(options, _args):
    if options('general.name') == 'local':
        raise Exception('Cannot terminate local cluster')
    
    terminateCluster(options('general.host'), options('general.name'), options('general.force'))
    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

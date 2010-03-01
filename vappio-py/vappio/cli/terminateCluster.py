#!/usr/bin/env python

import os

from igs.utils.cli import MissingOptionError, buildConfigN, notNone, defaultIfNone

from vappio.webservice.cluster import loadCluster
from vappio.cluster.control import terminateCluster

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', notNone),
    ]


URL = '/vappio/clusterInfo_ws.py'

def main(options, _args):
    if options('general.name') == 'local':
        raise Exception('Cannot terminate local cluster')
    
    cluster = loadCluster(options('general.host'), options('general.name'))
    terminateCluster(cluster)

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

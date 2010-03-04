#!/usr/bin/env python

import os

from igs.utils.cli import MissingOptionError, buildConfigN, notNone, defaultIfNone

from vappio.webservice.cluster import terminateCluster

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', notNone),
    ]


URL = '/vappio/clusterInfo_ws.py'

def main(options, _args):
    if options('general.name') == 'local':
        raise Exception('Cannot terminate local cluster')
    
    terminateCluster(options('general.host'), options('general.name'))
    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

#!/usr/bin/env python
##
# Provides useful URLs and other information about the cluster

from igs.utils import cli
from igs.utils.functional import identity

from vappio.webservice.cluster import loadCluster, listClusters

OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', cli.defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', cli.defaultIfNone('local')),
    ('partial', '-p', '--partial', 'Load partial data if a cluster is bad', identity, cli.BINARY),
    ('list', '-l', '--list', 'List all clusters', cli.defaultIfNone(False), cli.BINARY)
    ]

URL = '/vappio/clusterInfo_ws.py'

def instanceToList(i):
    return [i.instanceId or i.spotRequestId or 'Undefined', i.publicDNS or 'Undefined', i.state or 'Undefined']


def main(options, _args):
    if options('general.name'):
        cluster = loadCluster(options('general.host'), options('general.name'), options('general.partial'))


        print '\t'.join(['MASTER'] + instanceToList(cluster.master))
        for e in cluster.execNodes:
            print '\t'.join(['EXEC'] + instanceToList(e))
        for e in cluster.dataNodes:
            print '\t'.join(['DATA'] + instanceToList(e))

        print '\t'.join(['GANGLIA', 'http://%s/ganglia' % cluster.master.publicDNS])
        print '\t'.join(['ERGATIS', 'http://%s/ergatis' % cluster.master.publicDNS])
        print '\t'.join(['SSH', 'ssh %s %s@%s' % (cluster.config('ssh.options'), cluster.config('ssh.user'), cluster.master.publicDNS)])

    elif options('general.list'):
        for c in listClusters(options('general.host')):
            print '\t'.join(['CLUSTER', c])
    else:
        raise Exception('Failed to provide a cluster name or to list them')

if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))

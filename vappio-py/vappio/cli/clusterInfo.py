#!/usr/bin/env python
##
# Provides useful URLs and other information about the cluster

from igs.utils import cli
from igs.utils.functional import identity

from vappio.webservice.cluster import loadCluster, listClusters

OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', cli.defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', identity),
    ('partial', '-p', '--partial', 'Load partial data if a cluster is bad', identity, cli.BINARY),
    ('list', '-l', '--list', 'List all clusters', cli.defaultIfNone(False), cli.BINARY)
    ]

URL = '/vappio/clusterInfo_ws.py'

def main(options, _args):
    if options('general.name'):
        cluster = loadCluster(options('general.host'), options('general.name'), options('general.partial'))


        print '*** Cluster info ***'
        print 'Master IP: %s' % cluster.master.publicDNS
        print 'State: %s' % cluster.master.state
        print 'There are %3d exec nodes up' % len(cluster.execNodes)
        print '%3d are in "running" state' % len([c for c in cluster.execNodes if c.state == cluster.ctype.Instance.RUNNING])
        print 'There are %3d data nodes up' % len(cluster.dataNodes)
        print '%3d are in "running" state' % len([c for c in cluster.dataNodes if c.state == cluster.ctype.Instance.RUNNING])
        print
        print 'Useful URLs'
        print 'Ganglia: http://%s/ganglia' % cluster.master.publicDNS
        print 'Ergatis: http://%s/ergatis' % cluster.master.publicDNS
        print 'SSH: ssh %s %s@%s' % (cluster.config('ssh.options'), cluster.config('ssh.user'), cluster.master.publicDNS)
    elif options('general.list'):
        print '*** Available Clusters ***'
        print ' '.join(listClusters(options('general.host')))
    else:
        raise Exception('Failed to provide a cluster name or to list them')

if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))

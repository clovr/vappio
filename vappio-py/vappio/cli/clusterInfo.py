#!/usr/bin/env python
##
# Provides useful URLs and other information about the cluster

from igs.utils.cli import buildConfigN, notNone, defaultIfNone

from vappio.webservice.cluster import loadCluster

OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', notNone),
    ]

URL = '/vappio/clusterInfo_ws.py'

def main(options, _args):
    cluster = loadCluster(options('general.host'), options('general.name'))


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

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

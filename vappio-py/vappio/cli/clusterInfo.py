#!/usr/bin/env python
##
# Provides useful URLs and other information about the cluster
import os

from igs.utils.cli import buildConfigN, notNone

from vappio.cluster.persist import load

OPTIONS = [
    ('name', '', '--name', 'Name of cluster', notNone),
    ]

URL = '/vappio/clusterInfo_ws.py'

def main(options, _args):
    cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))


    masterIP = cluster.master.publicDNS

    print '*** Cluster info ***'
    print 'Master IP: %s' % masterIP
    print 'There are %3d exec nodes up' % len(cluster.execNodes)
    print 'There are %3d data nodes up' % len(cluster.dataNodes)
    print
    print 'Useful URLs'
    print 'Ganglia: http://%s/ganglia' % masterIP
    print 'Ergatis: http://%s/ergatis' % masterIP
    print 'SSH: ssh %s %s@%s' % (cluster.config('ssh.options'), cluster.config('ssh.user'), masterIP)

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

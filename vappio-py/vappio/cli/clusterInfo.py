#!/usr/bin/env python
##
# Provides useful URLs and other information about the cluster
import os

from igs.utils.cli import buildConfigN, notNone

from igs.utils.commands import runCommandGens
from igs.utils.logging import errorPrintS

from vappio.instance.control import runSystemInstanceA

from vappio.cluster.persist import load

OPTIONS = [
    ('name', '', '--name', 'Name of cluster (in this case the IP address of the master)', notNone),
    ]



def main(options, _args):
    cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))

    masterIP = cluster.master.publicDNS

    print '*** Cluster info ***'
    print 'Master IP: %s' % masterIP
    print 'There are %d slaves up' % len(cluster.slaves)
    print
    print 'Useful URLs'
    print 'Ganglia: http://%s/ganglia' % masterIP
    print 'Ergatis: http://%s/ergatis' % masterIP
    print 'SSH: ssh %s %s@%s' % (cluster.config('ssh.options'), cluster.config('ssh.user'), masterIP)

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

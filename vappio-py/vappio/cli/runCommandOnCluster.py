#!/usr/bin/env python
##
# Runs commands on the cluster

from igs.utils.cli import buildConfigN, notNone, defaultIfNone

from vappio.cluster.control import runCommandOnCluster

from vappio.webservice.cluster import loadCluster


OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', notNone),
    ('just_master', '-m', '--just_master', 'Just run the command on the master', defaultIfNone(False), True),
    ('command', '', '--cmd', 'Command to run', notNone)
    ]

def main(options, _args):
    cluster = loadCluster(options('general.host'), options('general.name'))
    runCommandOnCluster(cluster, options('general.command'), options('general.just_master'))
    

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

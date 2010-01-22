#!/usr/bin/env python
##
# Runs commands on the cluster
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone

from vappio.cluster.control import runCommandOnCluster

from vappio.cluster.persist import load

OPTIONS = [
    ('name', '', '--name', 'Name of cluster (in this case the IP address of the master)', notNone),
    ('just_master', '-m', '--just_master', 'Just run the command on the master', defaultIfNone(False), True),
    ('command', '', '--cmd', 'Command to run', notNone)
    ]




def main(options, _args):
    cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))

    runCommandOnCluster(cluster, options('general.command'), options('general.just_master'))
    

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

#!/usr/bin/env python
##
# Runs commands on the cluster
import os

from igs.utils.cli import buildConfigN, notNone

from igs.utils.commands import runCommandGens
from igs.utils.logging import errorPrintS

from vappio.instance.control import runSystemInstanceA

from vappio.cluster.persist import load

OPTIONS = [
    ('name', '', '--name', 'Name of cluster (in this case the IP address of the master)', notNone),
    ('just_master', '-m', '--just_master', 'Just run the command on the master', defaultIfNone(False), True),
    ('command', '', '--cmd', 'Command to run', notNone)
    ]


def runCommandOnInstance(i, conf, command):
    pr = runSystemInstanceA(i, command, None, errorPrintS,
                            user=conf('ssh.user'), options=conf('ssh.options'), log=True)
    yield pr

    if pr.exitCode != 0:
        raise ClusterError('Failed to run command on instance: ' + i.publicDNS)


def main(options, _args):
    cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))

    instances = [cluster.master]:

    if not options('general.just_master'):
        instances += cluster.slaves
        
    runCommandGens([runCommandOnInstance(i, cluster.config, options('general.command')) for i in instances])
    

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

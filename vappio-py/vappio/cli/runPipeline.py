#!/usr/bin/env python
##
# This just hands the work off to a remote machine
import optparse

from igs.utils.cli import buildConfigN, MissingOptionError, notNone

from igs.utils.config import configFromMap, configFromStream
from igs.utils.logging import errorPrintS, logPrintS

from vappio.instance.control import runSystemInstanceEx

from vappio.ec2 import control as ec2control

OPTIONS = [
    ('conf', '', '--conf', 'Name of config file', notNone),
    ('name', '', '--name', 'Name of cluster (host name of master)', notNone),
    ('pipeline', '', '--pipeline', 'Name of pipeline', notNone),
    ]

def getInstances(f):
    return [i for i in ec2control.listInstances() if f(i)]


def main(options, args):
    options = configFromMap({'general': {'options': args}}, options)
    
    instances = getInstances(lambda i : i.publicDNS == options('general.name'))
    if not instances:
        raise MissingOptionError('Did not provide a valid host')

    mastInst = instances[0]
    cmd = ['runPipeline_remote.py', options('general.pipeline')] + options('general.options')
    runSystemInstanceEx(mastInst, ' '.join(cmd), logPrintS, errorPrintS, user='root', options=options('ssh.options'), log=True)    
        

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS, usage='usage: %prog --name x --pipeline y [ -- options for pipeline]'))

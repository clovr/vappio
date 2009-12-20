#!/usr/bin/env python
##
# Uploads files to a cluster
import os
import time
import optparse

from igs.utils.cli import buildConfig, MissingOptionError, buildConfigN, notNone
from igs.utils.config import configFromMap, configFromStream
from igs.utils.ssh import scpToEx
from igs.utils.logging import errorPrintS
from igs.utils.functional import identity

from vappio.instance.control import runSystemInstanceEx

from vappio.ec2 import control as ec2control

OPTIONS = [
    ('conf', '', '--conf', 'Name of config file', notNone),
    ('name', '', '--name', 'Name of cluster (in this case the IP address of the master)', notNone),
    ('tag', '', '--tag', 'The uploaded files will be put into a file list tagged by this name', identity)
    ]


def getInstances(f):
    return [i for i in ec2control.listInstances() if f(i)]


def main(options, args):
    if len(args) <= 1:
        raise MissingOptionError('Must provide input files and output name')
    
    inpf = args[:-1]
    outf = args[-1]

    ##
    # Add some options
    options = configFromMap({'general': {
        'srcFiles': inpf,
        'destDir': outf,
        }}, options)
    
    instances = getInstances(lambda i : i.publicDNS == options('general.name'))
    if not instances:
        raise MissingOptionError('Did not provide a valid host')

    mastInst = instances[0]

    outDir = os.path.join('/mnt/staging', options('general.destDir'))
    
    runSystemInstanceEx(mastInst, 'mkdir -p ' + outDir, None, errorPrintS, user='root', options=options('ssh.options'), log=True)
    for f in options('general.srcFiles'):
        scpToEx(mastInst.publicDNS, f, outDir, user='root', options=options('ssh.options'), log=True)

    if options('general.tag'):
        tempFName = os.path.join('/tmp', str(time.time()))
        fout = open(tempFName, 'w')
        for f in options('general.srcFiles'):
            fout.write(os.path.join(outDir, os.path.basename(f)) + '\n')

        fout.close()
        runSystemInstanceEx(mastInst, 'mkdir -p /mnt/staging/tags', None, errorPrintS, user='root', options=options('ssh.options'), log=True)
        scpToEx(mastInst.publicDNS, tempFName, os.path.join('/mnt/staging/tags', options('general.tag')), user='root', options=options('ssh.options'), log=True)
        os.remove(tempFName)
        

if __name__ == '__main__':
    #main(buildConfig(cliParser(), cliMerger))
    main(*buildConfigN(OPTIONS))

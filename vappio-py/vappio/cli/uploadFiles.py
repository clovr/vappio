#!/usr/bin/env python
##
# Uploads files to a cluster
import os
import time
import optparse

from igs.utils.cli import buildConfig, MissingOptionError
from igs.utils.config import configFromMap, configFromStream
from igs.utils.ssh import scpToEx
from igs.utils.logging import errorPrintS

from vappio.instance.control import runSystemInstanceEx

from vappio.ec2 import control as ec2control

def cliParser():
    parser = optparse.OptionParser()

    parser.add_option('', '--conf', dest='conf', help='Name of config file to load')
    parser.add_option('', '--cluster', dest='cluster', help='Name of cluster to upload to (currently not used)')
    parser.add_option('', '--host', dest='host', help='Host of machine to upload to (will be deprecated once --cluster works')
    parser.add_option('', '--tag', dest='tag', help='Create a file list with the tagged name')

    return parser


def cliMerger(cliOptions, args):
    """
    args contains the list of files, the last argument is the output dir name
    """

    if len(args) <= 1:
        raise MissingOptionError('Failed to provided input files and an output name')

    if not cliOptions.host:
        raise MissingOptionError('Missing host of cluster machine')
    
    inpf = args[:-1]
    outf = args[-1]

    return configFromMap({
        'cluster': cliOptions.cluster,
        'host': cliOptions.host,
        'tag': cliOptions.tag,
        'srcFiles': inpf,
        'destDir': outf
        }, configFromStream(open(cliOptions.conf)))


def getInstances(f):
    return [i for i in ec2control.listInstances() if f(i)]


def main(options):
    instances = getInstances(lambda i : i.publicDNS == options('host'))
    if not instances:
        raise Exception('Did not provide a valid host')

    mastInst = instances[0]

    outDir = os.path.join('/mnt/staging', options('destDir'))
    
    runSystemInstanceEx(mastInst, 'mkdir -p ' + outDir, None, errorPrintS, user='root', options=options('ssh.options'), log=True)
    for f in options('srcFiles'):
        scpToEx(mastInst.publicDNS, f, outDir, user='root', options=options('ssh.options'), log=True)

    if options('tag'):
        tempFName = os.path.join('/tmp', str(time.time()))
        fout = open(tempFName, 'w')
        for f in options('srcFiles'):
            fout.write(os.path.join(outDir, os.path.basename(f)) + '\n')

        fout.close()
        runSystemInstanceEx(mastInst, 'mkdir -p /mnt/staging/tags', None, errorPrintS, user='root', options=options('ssh.options'), log=True)
        scpToEx(mastInst.publicDNS, tempFName, os.path.join('/mnt/staging/tags', options('tag')), user='root', options=options('ssh.options'), log=True)
        os.remove(tempFName)
        

if __name__ == '__main__':
    main(buildConfig(cliParser(), cliMerger))

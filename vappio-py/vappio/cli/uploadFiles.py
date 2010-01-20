#!/usr/bin/env python
##
# Uploads files to a cluster
import os
import time

from igs.utils.cli import buildConfigN, notNone, MissingOptionError

from vappio.ec2 import control as ec2control

from vappio.instance.transfer import uploadAndTag

from vappio.cluster.misc import getInstances

OPTIONS = [
    ('conf', '', '--conf', 'Name of config file', notNone),
    ('name', '', '--name', 'Name of cluster (in this case the IP address of the master)', notNone),
    ('tag', '', '--tag', 'The uploaded files will be put into a file list tagged by this name', notNone)
    ]

        
def main(options, args):
    if len(args) <= 1:
        raise MissingOptionError('Must provide input files and output name')
    
    instances = getInstances(lambda i : i.publicDNS == options('general.name'), ec2control)
    if not instances:
        raise MissingOptionError('Did not provide a valid host')

    mastInst = instances[0]

    srcFiles = args[:-1]
    outDir = args[-1]
    
    uploadAndTag(mastInst, options, options('general.tag'), srcFiles, outDir, log=True)

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

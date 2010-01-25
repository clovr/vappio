#!/usr/bin/env python
##
# Uploads files to a cluster
import os

from igs.utils.cli import buildConfigN, notNone, MissingOptionError

from vappio.instance.transfer import uploadAndTag

from vappio.cluster.persist import load, dump

OPTIONS = [
    ('name', '', '--name', 'Name of cluster', notNone),
    ('tag', '', '--tag', 'The uploaded files will be put into a file list tagged by this name', notNone)
    ]

        
def main(options, args):
    if len(args) < 1:
        raise MissingOptionError('Must provide input files')
    
    srcFiles = args

    cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))
    
    uploadAndTag(cluster.master, cluster.config, options('general.tag'), srcFiles, options('general.tag'), log=True)

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

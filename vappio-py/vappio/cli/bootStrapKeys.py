#!/usr/bin/env python
##
# Temporary program for loading keys into the proper location
import os

from igs.utils.cli import buildConfigN, notNone

from igs.utils.commands import runSystemEx

OPTIONS = [
    ('cert', '-c', '--cert', 'Path to cert', notNone),
    ('pk', '-p', '--pk', 'Path to private key', notNone),
    ('devel', '-d', '--devel', 'Path to devel1.pem', notNone)
    ]

def main(options, _args):
    runSystemEx('cp %s /tmp' % options('general.cert'))
    runSystemEx('cp %s /tmp' % options('general.pk'))
    if not os.path.exists('/mnt/devel1.pem'):
        runSystemEx('cp %s /mnt' % options('general.devel'))
    runSystemEx('chmod +r /tmp/*.pem')

    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

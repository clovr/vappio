#!/usr/bin/env python
##
# This creates a machine.conf file for the local machine.
# This is useful if you need to create a machine.conf for something coming up in Xen or VMWare
import sys

from igs.utils.cli import buildConfigN, defaultIfNone, notNone
from igs.utils.functional import compose
from igs.utils.commands import runSingleProgramEx
from igs.utils.logging import errorPrintS

from vappio.instance.config import createDataFile


OPTIONS = [
    ('conf', '', '--conf', 'Config file to load', notNone),
    ('mode', '-m', '--mode', 'The mode of this node type, defaults to MASTER', defaultIfNone('MASTER')),
    ##
    # if f is sys.stdout just return that, otherwise try to open f
    ('output', '-o', '--output', 'Output filename', notNone)
                                                    
    ]


def main(options, _args):
    res = []
    runSingleProgramEx('hostname -f', res.append, errorPrintS)
    localHost = ''.join(res).strip()
    outFile = createDataFile(options, [options('general.mode')], options('general.output'))
    open(outFile, 'a').write('MASTER_IP=' + localHost + '\n')

    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

#!/usr/bin/env python
##
# This just hands the work off to a remote machine
import sys

from twisted.python.reflect import namedAny, ModuleNotFound

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.logging import errorPrint

from vappio.ergatis.pipeline import runPipeline


OPTIONS = [
    ('pipeline', '-p', '--pipeline', 'Pipeline for which you want help displayed', notNone),
    ]


def main(options, _args):
    ##
    # Incredible hack right now
    sys.argv = [sys.argv[0]] + ['--help']
    try:
        pipeline = namedAny('vappio.pipelines.' + options('general.pipeline'))
        runPipeline(pipeline)
    except ModuleNotFound:
        errorPrint('The requested pipeline could not be found')

    

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

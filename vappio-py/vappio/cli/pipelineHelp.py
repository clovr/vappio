#!/usr/bin/env python
##
import sys

from twisted.python.reflect import namedModule

from igs.utils.cli import buildConfigN, notNone
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
        pipeline = namedModule('vappio.pipelines.' + options('general.pipeline'))
        runPipeline(None, pipeline)
    except ImportError:
        errorPrint('The requested pipeline could not be found')

    

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

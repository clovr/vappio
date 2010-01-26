#!/usr/bin/env python
##
# This is more of a stub program right now, it just handles blastn, but will be expanded
#
# This is meant to be run on the remote side
import sys

from twisted.python.reflect import namedModule

from igs.utils.logging import errorPrint, logPrint

from vappio.ergatis.pipeline import runPipeline

def main(_options):
    try:
        pipeline = namedModule('vappio.pipelines.' + sys.argv[1])
        sys.argv.pop(1)
        pipelineObj = runPipeline(pipeline)
        logPrint('Pipeline ID is: ' + pipelineObj.pid)
    except ImportError:
        errorPrint('The requested pipeline could not be found')


if __name__ == '__main__':
    main(None)
    

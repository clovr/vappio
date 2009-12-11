#!/usr/bin/env python
##
# This is more of a stub program right now, it just handles blastn, but will be expanded
#
# This is meant to be run on the remote side
import sys

from vappio import pipelines


PIPELINES = {
    'blastn': pipelines.blastn
    }

def main(options):
    if sys.argv[0] in PIPELINES:
        pipeline = PIPELINES[sys.argv[0]]
        sys.argv.pop(0)
        pipeline.runPipeline()


if __name__ == '__main__':
    main(None)
    

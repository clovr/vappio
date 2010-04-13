#!/usr/bin/env python
##
# This is a simpel hack script to delete a pipeline from monogodb so a new one can be
# run with the same name.  This script is really mostly for testing and it only runs
# on the local machine

import pymongo

from igs.utils.cli import buildConfigN, notNone

OPTIONS = [
    ('pipeline', '-p', '--pipeline-name', 'Name of pipeline to delete', notNone),
    ]



def main(options, _args):
    pipelines = pymongo.Connection().clovr.pipelines

    pipelines.remove(dict(name=options('general.pipeline')))


if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))
    

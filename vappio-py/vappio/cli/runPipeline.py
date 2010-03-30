#!/usr/bin/env python
##
# Runs a pipeline throuhg the webservice call
from igs.utils.cli import buildConfigN, defaultIfNone, notNone

from igs.utils.logging import logPrint

from vappio.webservice.pipeline import runPipeline

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact, defaults to localhost', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', notNone),
    ('pipeline', '-p', '--pipeline', 'Type of pipeline', notNone),
    ('pipeline_name', '-n', '--pipeline-name', 'Name to give the pipeline', notNone)
    ]

URL = '/vappio/runPipeline_ws.py'

def main(options, args):

    res = runPipeline(options('general.host'),
                      options('general.name'),
                      options('general.pipeline'),
                      options('general.pipeline_name'),
                      args)

    logPrint('Pipeline Id: ' + str(res))

    

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS, usage='usage: %prog --name x --pipeline y [ -- options for pipeline]'))

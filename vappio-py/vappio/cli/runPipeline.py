#!/usr/bin/env python
##
# Runs a pipeline throuhg the webservice call
from igs.utils.cli import buildConfigN, defaultIfNone, notNone
from igs.utils import config
from igs.utils import functional as func

from vappio.webservice import pipeline

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact, defaults to localhost', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', defaultIfNone('local')),
    ('pipeline', '-p', '--pipeline', 'Type of pipeline', notNone),
    ('pipeline_name', '-n', '--pipeline-name', 'Name to give the pipeline', notNone),
    ('pipeline_config', '', '--pipeline-config', 'Config file to use for the pipeline', func.identity),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end', defaultIfNone(False), True),
    ]

URL = '/vappio/runPipeline_ws.py'

def main(options, args):
    if options('general.pipeline_config') and args:
        raise Exception('--pipeline-config and arguments are mutually exclusive')
    
    if args:
        taskName = pipeline.runPipeline(options('general.host'),
                                        options('general.name'),
                                        options('general.pipeline'),
                                        options('general.pipeline_name'),
                                        args)
    else:
        taskName = pipeline.runPipelineConfig(options('general.host'),
                                              options('general.name'),
                                              options('general.pipeline'),
                                              options('general.pipeline_name'),
                                              config.configFromStream(open(options('general.pipeline_config')), lazy=True))

    if options('general.print_task_name'):
        print taskName

        
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS, usage='usage: %prog --name x --pipeline y [ -- options for pipeline]'))

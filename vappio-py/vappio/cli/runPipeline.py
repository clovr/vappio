#!/usr/bin/env python
##
# Runs a pipeline throuhg the webservice call
from igs.utils import cli
from igs.utils import config
from igs.utils import functional as func

from vappio.webservice import pipeline

from vappio.tasks.utils import runTaskStatus

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact, defaults to localhost', cli.defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', cli.defaultIfNone('local')),
    ('pipeline', '-p', '--pipeline', 'Type of pipeline', cli.notNone),
    ('pipeline_name', '-n', '--pipeline-name', 'Name to give the pipeline', cli.notNone),
    ('pipeline_config', '', '--pipeline-config', 'Config file to use for the pipeline', func.identity),
    ('pipeline_queue', '-q', '--pipeline-queue', 'Queue to use, not required', func.identity),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end', cli.defaultIfNone(False), cli.BINARY),
    ]

URL = '/vappio/runPipeline_ws.py'

def main(options, args):
    if options('general.pipeline_config') and args:
        raise Exception('--pipeline-config and arguments are mutually exclusive')
    
    if args:
        # taskName = pipeline.runPipeline(options('general.host'),
        #                                 options('general.name'),
        #                                 options('general.pipeline'),
        #                                 options('general.pipeline_name'),
        #                                 args,
        #                                 options('general.pipeline_queue'))
        raise Exception('No longer supporting passing arguments, all must be done through config files')
    else:
        conf = config.configFromStream(open(options('general.pipeline_config')), lazy=True)
        if options('general.pipeline') == 'clovr_wrapper':
            conf = config.configFromMap({'pipeline.PIPELINE_WRAPPER_NAME': options('general.pipeline_name')}, base=conf, lazy=True)
        taskName = pipeline.runPipelineConfig(options('general.host'),
                                              options('general.name'),
                                              options('general.pipeline'),
                                              options('general.pipeline_name'),
                                              conf,
                                              options('general.pipeline_queue'))


    if options('general.print_task_name'):
        print taskName
    else:
        runTaskStatus(taskName)
    
        
if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS, usage='usage: %prog --name x --pipeline y [ -- options for pipeline]'))

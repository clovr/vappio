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
    ('pipeline', '-p', '--pipeline', 'Type of pipeline', func.identity),
    ('pipeline_name', '-n', '--pipeline-name', 'Name to give the pipeline', cli.notNone),
    ('pipeline_config', '', '--pipeline-config', 'Config file to use for the pipeline', func.identity),
    ('pipeline_resume', '', '--resume', 'Resume pipeline if it is not running or completed', cli.defaultIfNone(False), cli.BINARY),
    ('pipeline_queue', '-q', '--pipeline-queue', 'Queue to use, not required', func.identity),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end', cli.defaultIfNone(False), cli.BINARY),
    ]

URL = '/vappio/runPipeline_ws.py'

def main(options, args):
    if not options('general.pipeline_config') and not options('general.pipeline_resume'):
        raise Exception('Must provide at least either a pipeline config or that you wish to resume')

    if not options('general.pipeline_resume') and not options('general.pipeline'):
        raise Exception('Must provide a pipeline if not resuming')
    
    if args:
        raise Exception('No longer supporting passing arguments, all must be done through config files')
    elif options('general.pipeline_config'):
        conf = config.configFromStream(open(options('general.pipeline_config')), lazy=True)
        taskName = pipeline.runPipelineConfig(options('general.host'),
                                              options('general.name'),
                                              options('general.pipeline'),
                                              options('general.pipeline_name'),
                                              conf,
                                              options('general.pipeline_queue'),
                                              resume=options('general.pipeline_resume'))
    elif options('general.pipeline_resume'):
        taskName = pipeline.runPipelineConfig(options('general.host'),
                                              options('general.name'),
                                              options('general.pipeline'),
                                              options('general.pipeline_name'),
                                              config.configFromMap({}),
                                              options('general.pipeline_queue'),
                                              resume=options('general.pipeline_resume'))
    else:
        raise Exception('I am not sure how I got here')


    if options('general.print_task_name'):
        print taskName
    else:
        runTaskStatus(taskName)
    
        
if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS, usage='usage: %prog --name x --pipeline y --pipeline-config=CONFIG_FILE'))

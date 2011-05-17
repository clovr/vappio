#!/usr/bin/env python
##
# Runs a pipeline throuhg the webservice call
import sys

from igs.utils import cli
from igs.utils import config
from igs.utils import functional as func

from vappio.webservice import pipeline

from vappio.tasks.utils import runTaskStatus

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact, defaults to localhost', cli.defaultIfNone('localhost')),
    ('cluster', '', '--cluster', 'Name of cluster', cli.defaultIfNone('local')),
    ('bare_run', '', '--bare', 'Do not run with a wrapper', cli.defaultIfNone(False), cli.BINARY),
    ('pipeline_parent', '', '--pipeline-parent', 'Name of parent pipeline', func.identity),
    ('pipeline_config', '', '--pipeline-config', 'Config file to use for the pipeline', cli.notNone),
    #('pipeline_resume', '', '--resume', 'Name of pipeline to be resumed', func.identity),
    ('pipeline_queue', '-q', '--pipeline-queue', 'Queue to use, not required', func.identity),
    ('validate',
     '-v',
     '--validate',
     'Do a simple type check on the config file and exit without running',
     cli.defaultIfNone(False),
     cli.BINARY),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end', cli.defaultIfNone(False), cli.BINARY),
    ]


def main(options, args):
    conf = config.configFromStream(open(options('general.pipeline_config')), lazy=True)

    ret = pipeline.validatePipelineConfig(options('general.host'),
                                          options('general.cluster'),
                                          options('general.bare_run'),
                                          conf)
    if ret['errors']:
        for e in ret['errors']:
            print '\t'.join(['ERROR', ','.join(e['keys']), e['message']])
        # Exit with an error
        sys.exit(1)

    if not options('general.validate'):
        p = pipeline.runPipeline(options('general.host'),
                                 options('general.cluster'),
                                 options('general.pipeline_parent'),
                                 options('general.bare_run'),
                                 conf,
                                 options('general.pipeline_queue'))
        if options('general.print_task_name'):
            print p['task_name']
        else:
            runTaskStatus(p['task_name'])
        
if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS, usage='usage: %prog --name x --pipeline y --pipeline-config=CONFIG_FILE'))

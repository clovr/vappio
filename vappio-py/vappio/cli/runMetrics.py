#!/usr/bin/env python
from igs.utils import cli
from igs.utils import functional as func

from vappio.webservice import pipeline

from vappio.tasks.task import TASK_FAILED
from vappio.tasks.utils import blockOnTask

OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', cli.defaultIfNone('localhost')),    
    ('name', '', '--name', 'Name of cluster to run on', cli.notNone),
    ('block', '-b', '--block', 'Block on task name', cli.defaultIfNone(False), cli.BINARY),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end',
     cli.defaultIfNone(False), cli.BINARY),
    ('pipeline', '', '--pipeline-name', 'Name of pipeline to run against', func.identity),
    ('conf', '-c', '--conf', 'Add config options, multiple allowed in style -c key=value -c key=value',
     func.identity, cli.LIST)
    ]


def main(options, args):
    metrics = args
    conf = dict([v.split('=', 1) for v in options('general.conf', default=[])])
    if options('general.pipeline'):
        metrics = 'get-pipeline-conf | ' + metrics
        conf['PIPELINE_NAME'] = options('general.pipeline')

    taskName = pipeline.runMetrics(options('general.host'), options('general.name'), conf, metrics)

    if options('general.block'):
        state = blockOnTask(options('general.host'), options('general.name'), taskName)
        if state == TASK_FAILED:
            raise Exception('Running metric failed')

    if options('general.print_task_name'):
        print taskName

    

if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS, usage='%prog --name=cluster [options] "metric1 | metric2 | .. | metricn"\nQuotes are important'))

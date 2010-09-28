#!/usr/bin/env python
from igs.utils import cli
from igs.utils import functional as func

from vappio.webservice import pipeline

from vappio.tasks.utils import runTaskStatus

OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', cli.defaultIfNone('localhost')),    
    ('name', '', '--name', 'Name of cluster to run on', cli.defaultIfNone('local')),
    ('block', '-b', '--block', 'Block on task name', cli.defaultIfNone(False), cli.BINARY),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end',
     cli.defaultIfNone(False), cli.BINARY),
    ('pipeline', '', '--pipeline-name', 'Name of pipeline to run against', func.identity),
    ('config', '-c', '', 'Add config options, multiple allowed in style -c key=value -c key=value',
     cli.defaultIfNone([]), cli.LIST)
    ]


def main(options, args):
    metrics = args[0]
    conf = dict([v.split('=', 1) for v in options('general.config', default=[])])
    if options('general.pipeline'):
        if metrics:
            metrics = 'get-pipeline-conf %s | %s | set-pipeline-conf %s' % (options('general.pipeline'), metrics, options('general.pipeline'))
        else:
            metrics = 'get-pipeline-conf %s | set-pipeline-conf %s' % (options('general.pipeline'), options('general.pipeline'))

    taskName = pipeline.runMetrics(options('general.host'), options('general.name'), conf, metrics)
    
    if options('general.print_task_name'):
        print taskName
    else:
        runTaskStatus(taskName)
    

if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS, usage='%prog --name=cluster [options] "metric1 | metric2 | .. | metricn"\nQuotes are important'))

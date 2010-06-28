#!/usr/bin/env python
##
# Runs a pipeline throuhg the webservice call
from igs.utils.cli import buildConfigN, defaultIfNone, notNone

from vappio.webservice.pipeline import runPipeline

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact, defaults to localhost', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', notNone),
    ('pipeline', '-p', '--pipeline', 'Type of pipeline', notNone),
    ('pipeline_name', '-n', '--pipeline-name', 'Name to give the pipeline', notNone),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end', defaultIfNone(False), True),
    ]

URL = '/vappio/runPipeline_ws.py'

def main(options, args):
    taskName = runPipeline(options('general.host'),
                           options('general.name'),
                           options('general.pipeline'),
                           options('general.pipeline_name'),
                           args)

    if options('general.print_task_name'):
        print taskName

        
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS, usage='usage: %prog --name x --pipeline y [ -- options for pipeline]'))

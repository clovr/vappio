#!/usr/bin/env python

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.functional import identity

from vappio.webservice.tag import downloadTag

from vappio.tasks.utils import runTaskStatus


OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', defaultIfNone('localhost')),
    ('tag_name', '', '--tag-name', 'Name of tag to upload', notNone),
    ('src_cluster', '', '--src-cluster', 'Name of source cluster', notNone),
    ('dst_cluster', '', '--dst-cluster', 'Name of dest cluster, hardcoded to local for now', lambda _ : 'local'),
    ('block', '-b', '--block', 'Block until download is complete', identity, True),
    ('expand', '', '--expand', 'Expand files', defaultIfNone(False), True),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end', defaultIfNone(False), True),    
    ]

def main(options, files):
    taskName = downloadTag(options('general.host'),
                           options('general.tag_name'),
                           options('general.src_cluster'),
                           options('general.dst_cluster'),
                           options('general.expand'))

    if options('general.print_task_name'):
        print taskName
    else:
        runTaskStatus(taskName)


if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))
    


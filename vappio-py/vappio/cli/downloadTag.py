#!/usr/bin/env python

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils import functional as func

from vappio.webservice.tag import downloadTag

from vappio.tasks.utils import runTaskStatus


OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', defaultIfNone('localhost')),
    ('tag_name', '', '--tag-name', 'Name of tag to upload', notNone),
    ('src_cluster', '', '--src-cluster', 'Name of source cluster', notNone),
    ('dst_cluster', '', '--dst-cluster', 'Name of dest cluster, hardcoded to local for now', func.const('local')),
    ('output_dir', '', '--output-dir', 'Name of directory to download to', func.identity),
    ('block', '-b', '--block', 'Block until download is complete', func.identity, cli.BINARY),
    ('expand', '', '--expand', 'Expand files', defaultIfNone(False), cli.BINARY),
    ('compress', '', '--compress', 'Compress files', func.identity, cli.BINARY),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end', defaultIfNone(False), cli.BINARY),
    ]

def main(options, files):
    taskName = downloadTag(options('general.host'),
                           options('general.tag_name'),
                           options('general.src_cluster'),
                           options('general.dst_cluster'),
                           options('general.output_dir'),
                           options('general.expand'),
                           options('general.compress'))

    if options('general.print_task_name'):
        print taskName
    else:
        runTaskStatus(taskName)


if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))
    


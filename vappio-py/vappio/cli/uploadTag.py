#!/usr/bin/env python

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.functional import identity

from vappio.webservice.files import uploadTag

from vappio.tasks.task import TASK_FAILED
from vappio.tasks.utils import blockOnTask


OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', defaultIfNone('localhost')),
    ('tag_name', '', '--tag-name', 'Name of tag to upload', notNone),
    ('src_cluster', '', '--src-cluster', 'Name of source cluster, hardcoded to local for now', lambda _ : 'local'),
    ('dst_cluster', '', '--dst-cluster', 'Name of dest cluster', notNone),
    ('block', '-b', '--block', 'Block until cluster is up', identity, True),
    ('expand', '', '--expand', 'Expand files', defaultIfNone(False), True),
    ]

def main(options, _files):
    taskName = uploadTag(options('general.host'),
                         options('general.tag_name'),
                         options('general.src_cluster'),
                         options('general.dst_cluster'),
                         options('general.expand'))

    if options('general.block'):
        state = blockOnTask(options('general.host'), options('general.src_cluster'), taskName)
        if state == TASK_FAILED:
            raise Exception('Starting cluster failed')
    

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))
    


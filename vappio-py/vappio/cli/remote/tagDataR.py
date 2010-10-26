#!/usr/bin/env python
import json
from igs.utils import cli
from igs.utils import functional as func

from vappio.core.error_handler import runCatchError, mongoFail
from vappio.webservice.cluster import loadCluster
from vappio.tags.tagfile import tagData
from vappio.tasks import task
from vappio.tasks import utils as task_utils

OPTIONS = [
    ('tag_name', '', '--tag-name', 'Name of the tag', cli.notNone),
    ('task_name', '', '--task-name', 'Name of task', cli.notNone),
    ('tag_base_dir', '', '--tag-base-dir', 'Base dir of tag', func.identity),
    ('recursive', '-r', '--recursive', 'If file is a direcotry, recursively add files', cli.defaultIfNone(False), cli.BINARY),
    ('expand', '-e', '--expand', 'If file is an archive (.bz2, .tar.gz, .tgz), expand it', cli.defaultIfNone(False), cli.BINARY),
    ('compress', '-c', '--compress',
     'Make a tarball of the tagged results.  This should be the directory to put the tarball. This is not mutually exclusive with --expand',
     func.identity),
    ('append', '-a', '--append', 'Append files to the current file list, this will not add duplicates. The overwrite option supercedes this.', cli.defaultIfNone(False), cli.BINARY),
    ('overwrite', '-o', '--overwrite', 'Overwrite tag if it already exists', cli.defaultIfNone(False), cli.BINARY),
    ('metadata', '', '--metadata', 'JSON Encoded dictionary representing metadata', cli.defaultIfNone('{}'))
    ]

RESTRICTED_DIRS = ['/bin/',
                   '/boot/',
                   '/dev/',
                   '/etc/',
                   '/home/',
                   '/lib/',
                   '/mnt/keys/',
                   '/mnt/vappio-conf/',
                   '/mnt/user-scripts/',
                   '/proc/',
                   '/root/',
                   '/sbin/',
                   '/tmp/'
                   '/usr/',
                   '/var/',
]

def restrictDirs(f):
    for d in RESTRICTED_DIRS:
        if f.startswith(d):
            return False

    return True

def main(options, files):
    tsk = task.updateTask(task.loadTask(options('general.task_name')
                                        ).setState(task.TASK_RUNNING
                                                   ).addMessage(task.MSG_SILENT, 'Starting tagging'))


    cluster = loadCluster('localhost', 'local')
    tagData(cluster.config('dirs.tag_dir'),
            options('general.tag_name'),
            options('general.tag_base_dir'),
            files,
            recursive=options('general.recursive'),
            expand=options('general.expand'),
            compress=options('general.compress'),
            append=options('general.append'),
            overwrite=options('general.overwrite'),
            metadata=json.loads(options('general.metadata').decode("string_escape")),
            filterF=restrictDirs)
    tsk = tsk.progress().addMessage(task.MSG_NOTIFICATION, 'Tagging complete').setState(task.TASK_COMPLETED)
    task.updateTask(tsk)


if __name__ == '__main__':
    runCatchError(lambda : task_utils.runTaskMain(main,
                                                  *cli.buildConfigN(OPTIONS)),
                  mongoFail(dict(action='tagData')))

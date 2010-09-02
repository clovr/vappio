#!/usr/bin/env python
import json
from igs.utils import cli
from igs.utils import functional as func
from igs.utils import errors

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
    ('append', '-a', '--append', 'Append files to the current file list, this will not add duplicates. The overwrite option supercedes this.', cli.defaultIfNone(False), cli.BINARY),
    ('overwrite', '-o', '--overwrite', 'Overwrite tag if it already exists', cli.defaultIfNone(False), cli.BINARY),
    ('metadata', '', '--metadata', 'JSON Encoded dictionary representing metadata', cli.defaultIfNone('{}'))
    ]


    

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
            append=options('general.append'),
            overwrite=options('general.overwrite'),
            metadata=json.loads(options('general.metadata')))
    tsk = tsk.progress().setState(task.TASK_COMPLETED)
    task.updateTask(tsk)


if __name__ == '__main__':
    runCatchError(lambda : task_utils.runTaskMain(main,
                                                  *cli.buildConfigN(OPTIONS)),
                  mongoFail(dict(action='tagData')))

#!/usr/bin/env python
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone, restrictValues
from igs.utils.functional import identity

from vappio.core.error_handler import runCatchError, mongoFail
from vappio.webservice.cluster import loadCluster
from vappio.tags.tagfile import tagData
from vappio.tasks import task

OPTIONS = [
    ('tag_name', '', '--tag-name', 'Name of the tag', notNone),
    ('task_name', '', '--task-name', 'Name of task', notNone),
    ('tag_base_dir', '', '--tag-base-dir', 'Base dir of tag', identity),
    ('recursive', '-r', '--recursive', 'If file is a direcotry, recursively add files', defaultIfNone(False), True),
    ('expand', '-e', '--expand', 'If file is an archive (.bz2, .tar.gz, .tgz), expand it', defaultIfNone(False), True),
    ('append', '-a', '--append', 'Append files to the current file list, this will not add duplicates. The overwrite option supercedes this.', defaultIfNone(False), True),
    ('overwrite', '-o', '--overwrite', 'Overwrite tag if it already exists', defaultIfNone(False), True)
    ]


    

def main(options, files):
    tsk = task.loadTask(options('general.task_name'))
    tsk = task.setState(tsk, task.TASK_RUNNING)
    tsk = task.addMessage(tsk, task.MSG_SILENT, 'Starting tagging')
    tsk = task.updateTask(tsk)

    try:
        cluster = loadCluster('localhost', 'local')
        tagData(cluster.config('dirs.tag_dir'),
                options('general.tag_name'),
                options('general.tag_base_dir'),
                files,
                recursive=options('general.recursive'),
                expand=options('general.expand'),
                append=options('general.append'),
                overwrite=options('general.overwrite'))
        tsk = task.progress(tsk)
        tsk = task.setState(tsk, task.TASK_COMPLETED)
    except Exception, err:
        tsk = task.setState(tsk, task.TASK_FAILED)
        tsk = task.addMessage(tsk, task.MSG_ERROR, str(err))

    tsk = task.updateTask(tsk)

    


if __name__ == '__main__':
    runCatchError(lambda : main(*buildConfigN(OPTIONS)),
                  mongoFail(dict(action='tagData')))

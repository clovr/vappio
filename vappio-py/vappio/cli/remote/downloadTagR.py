#!/usr/bin/env python

from igs.utils.cli import buildConfigN, notNone, defaultIfNone, restrictValues
from igs.utils import errors

from vappio.core.error_handler import runCatchError, mongoFail
from vappio.webservice.cluster import loadCluster
from vappio.webservice.tag import tagData
from vappio.tags.transfer import downloadTag

from vappio.tasks import task
from vappio.tasks.utils import blockOnTaskAndForward

OPTIONS = [
    ('tag_name', '', '--tag-name', 'Name of tag to transfer', notNone),
    ('task_name', '', '--task-name', 'Name of task', notNone),    
    ('src_cluster', '', '--src-cluster', 'Name of source cluster', notNone),
    ('dst_cluster', '', '--dst-cluster', 'Name of dest cluster, hardcoded to local for now', lambda _ : 'local'),
    ('expand', '', '--expand', 'Expand files', defaultIfNone(False), True)
    ]


def main(options, _args):
    tsk = task.updateTask(task.loadTask(options('general.task_name')
                                        ).setState(task.TASK_RUNNING
                                                   ).addMessage(task.MSG_SILENT, 'Starting download'))

    try:
        srcCluster = loadCluster('localhost', options('general.src_cluster'))
        dstCluster = loadCluster('localhost', options('general.dst_cluster'))
        fileList = downloadTag(srcCluster, dstCluster, options('general.tag_name'))
        tsk = task.updateTask(tsk.progress())
        tagTaskName = tagData('localhost',
                              options('general.dst_cluster'),
                              options('general.tag_name'),
                              None,
                              fileList,
                              False,
                              options('general.expand'),
                              False,
                              True)
        endState, tsk = blockOnTaskAndForward('localhost',
                                              options('general.dst_cluster'),
                                              tagTaskName,
                                              tsk)
        if endState == task.TASK_FAILED:
            tsk = task.updateTask(tsk.setState(task.TASK_FAILED))
        else:
            tsk = task.updateTask(tsk.progress().setState(task.TASK_COMPLETED))
    except Exception, err:
        tsk = tsk.setState(task.TASK_FAILED).addException(str(err), err, errors.getStacktrace())        


if __name__ == '__main__':
    runCatchError(lambda : main(*buildConfigN(OPTIONS)),
                  mongoFail(dict(action='uploadTag')))

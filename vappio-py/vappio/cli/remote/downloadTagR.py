#!/usr/bin/env python

from igs.utils import cli
from igs.utils import errors
from igs.utils import functional as func

from vappio.core.error_handler import runCatchError, mongoFail
from vappio.webservice.cluster import loadCluster
from vappio.webservice import tag
from vappio.tags.transfer import downloadTag

from vappio.tasks import task
from vappio.tasks import utils as task_utils

OPTIONS = [
    ('tag_name', '', '--tag-name', 'Name of tag to transfer', cli.notNone),
    ('task_name', '', '--task-name', 'Name of task', cli.notNone),
    ('src_cluster', '', '--src-cluster', 'Name of source cluster', cli.notNone),
    ('dst_cluster', '', '--dst-cluster', 'Name of dest cluster, hardcoded to local for now', func.const('local')),
    ('output_dir', '', '--output-dir', 'Name of output dir', func.identity),
    ('expand', '', '--expand', 'Expand files', cli.defaultIfNone(False), True),
    ('compress', '', '--compress', 'Compress files', func.identity)
    ]


def main(options, _args):
    tsk = task.updateTask(task.loadTask(options('general.task_name')
                                        ).setState(task.TASK_RUNNING
                                                   ).addMessage(task.MSG_SILENT, 'Starting download'))

    srcCluster = loadCluster('localhost', options('general.src_cluster'))
    dstCluster = loadCluster('localhost', options('general.dst_cluster'))
    
    tagFile = tag.queryTag('localhost', options('general.src_cluster'), options('general.tag_name'))

    metadataKeys = [k.split('.', 1)[1] for k in tagFile.keys() if k.startswith('metadata.')]
    metadata = dict([(k, tagFile('metadata.' + k)) for k in metadataKeys])


    fileTag = downloadTag(srcCluster,
                          dstCluster,
                          options('general.tag_name'),
                          dstDir=options('general.output_dir'),
                          baseDir=metadata.get('tag_base_dir', None))
    tsk = task.updateTask(tsk.progress())

    if options('general.compress'):
        compress = os.path.split(fileTag('metadata.tag_base_dir'))[0]
    else:
        compress = None
    
    tagTaskName = tag.tagData(host='localhost',
                              name=options('general.dst_cluster'),
                              tagName=options('general.tag_name'),
                              tagBaseDir=fileTag('metadata.tag_base_dir'),
                              files=fileTag('files'),
                              recursive=False,
                              expand=options('general.expand'),
                              compress=compress
                              append=False,
                              overwrite=True,
                              metadata=metadata)
    endState, tsk = task_utils.blockOnTaskAndForward('localhost',
                                                     options('general.dst_cluster'),
                                                     tagTaskName,
                                                     tsk)
    if endState == task.TASK_FAILED:
        raise Exception('Taging failed')
    else:
        tsk = task.updateTask(tsk.progress().addMessage(task.MSG_NOTIFICATION, 'Download complete'))


if __name__ == '__main__':
    runCatchError(lambda : task_utils.runTaskMain(main,
                                                  *cli.buildConfigN(OPTIONS)),
                  mongoFail(dict(action='uploadTag')))

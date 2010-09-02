#!/usr/bin/env python
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.ssh import scpToEx
from igs.utils import errors

from vappio.core.error_handler import runCatchError, mongoFail
from vappio.instance.control import runSystemInstanceEx
from vappio.webservice.cluster import loadCluster
from vappio.webservice.tag import tagData, realizePhantom
from vappio.tags.transfer import uploadTag
from vappio.tags import tagfile

from vappio.tasks import task
from vappio.tasks import utils as task_utils

OPTIONS = [
    ('tag_name', '', '--tag-name', 'Name of tag to transfer', notNone),
    ('task_name', '', '--task-name', 'Name of task', notNone),
    ('src_cluster', '', '--src-cluster', 'Name of source cluster, hardcoded to local for now', lambda _ : 'local'),
    ('dst_cluster', '', '--dst-cluster', 'Name of dest cluster', notNone),
    ('expand', '', '--expand', 'Expand files', defaultIfNone(False), True),
    ]


def main(options, _args):
    tsk = task.updateTask(task.loadTask(options('general.task_name')
                                        ).setState(task.TASK_RUNNING
                                                   ).addMessage(task.MSG_SILENT, 'Starting uploadTag'))

    try:
        srcCluster = loadCluster('localhost', options('general.src_cluster'))
        dstCluster = loadCluster('localhost', options('general.dst_cluster'))
        tagFileName = os.path.join(srcCluster.config('dirs.tag_dir'), options('general.tag_name'))
        tagFile = tagfile.loadTagFile(tagFileName)
    except tagfile.MissingTagFileError, err:
        tsk = tsk.setState(task.TASK_FAILED).addException('Could not find tag: ' + str(err), err, errors.getStacktrace())
        raise
    
    if tagfile.isPhantom(tagFile):
        tsk = task.updateTask(tsk.addMessage(task.MSG_SILENT, 'Tag is phantom, uploading tag'))

        scpToEx(dstCluster.master.publicDNS,
                os.path.join(srcCluster.config('dirs.tag_dir'), options('general.tag_name') + '.phantom'),
                os.path.join(dstCluster.config('dirs.tag_dir'), options('general.tag_name') + '.phantom'),
                user=srcCluster.config('ssh.user'),
                options=srcCluster.config('ssh.options'),
                log=True)
        
        # Upload any files this tag depends on
        for f in tagFile('phantom.depends_on', default='').split():
            runSystemInstanceEx(dstCluster.master,
                                'mkdir -p ' + os.path.dirname(f),
                                stdoutf=None,
                                stderrf=None,
                                user=srcCluster.config('ssh.user'),
                                options=srcCluster.config('ssh.options'),
                                log=True)
            scpToEx(dstCluster.master.publicDNS,
                    f,
                    f,
                    user=srcCluster.config('ssh.user'),
                    options=srcCluster.config('ssh.options'),
                    log=True)
            
        tsk = task.updateTask(tsk.progress().addMessage(task.MSG_SILENT, 'realizing phantom tag'))
        
        realizeTask = realizePhantom('localhost', dstCluster.name, options('general.tag_name'))
        endState, tsk = task_utils.blockOnTaskAndForward('localhost',
                                                         options('general.dst_cluster'),
                                                         realizeTask,
                                                         tsk)

        if endState == task.TASK_COMPLETED:
            tsk = tsk.progress().setState(task.TASK_COMPLETED).addMessage(task.MSG_SILENT, 'Done realizing')
        else:
            tsk = tsk.setState(task.TASK_FAILED)

        tsk = task.updateTask(tsk)
        
    else:
        ##
        # This should be fixed, right now there is a disconnect between what uploadTag
        # does in terms of where it places its data and then how tagData
        # should be called.  Perhaps these two calls should be placed into their
        # own call?
        # Perhaps uploadTag should return a tag data structure and then tagData should take a tag
        # to be put on the remote box?  Not sure yet, leaning towards the latter
        tsk = task.updateTask(tsk.addMessage(task.MSG_SILENT, 'Uploading tag contents'))

        fileList = uploadTag(srcCluster, dstCluster, options('general.tag_name'), tagFile)
        tsk = task.updateTask(tsk.progress().addMessage(task.MSG_SILENT, 'Upload complete, tagging'))

        metadataKeys = [k.split('.', 1)[1] for k in tagFile.keys() if k.startswith('metadata.')]
        metadata = dict([(k, tagFile('metadata.' + k)) for k in metadataKeys])

        tagTask = tagData('localhost',
                          options('general.dst_cluster'),
                          options('general.tag_name'),
                          os.path.join(dstCluster.config('dirs.tag_dir'), options('general.tag_name')),
                          fileList,
                          False,
                          options('general.expand'),
                          False,
                          True,
                          metadata)
        endState, tsk = task_utils.blockOnTaskAndForward('localhost',
                                                         options('general.dst_cluster'),
                                                         tagTask,
                                                         tsk)

        if endState == task.TASK_COMPLETED:
            tsk = tsk.progress().setState(task.TASK_COMPLETED).addMessage(task.MSG_SILENT, 'Tag complete')
        else:
            tsk = tsk.setState(task.TASK_FAILED)
            
        tsk = task.updateTask(tsk)
        
if __name__ == '__main__':
    runCatchError(lambda : task_utils.runTaskMain(main,
                                                  *buildConfigN(OPTIONS)),
                  mongoFail(dict(action='uploadTag')))

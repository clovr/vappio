#!/usr/bin/env python
import os

from igs.utils.cli import buildConfigN, notNone
from igs.utils.commands import runSystemEx
from igs.utils import errors

from vappio.core.error_handler import runCatchError, mongoFail
from vappio.webservice.cluster import loadCluster
from vappio.webservice.tag import tagData
from vappio.tags import tagfile

from vappio.tasks import task
from vappio.tasks import utils as task_utils

OPTIONS = [
    ('tag_name', '', '--tag-name', 'Name of the tag', notNone),
    ('task_name', '', '--task-name', 'Name of task', notNone)
    ]


    

def main(options, _args):
    tsk = task.updateTask(task.loadTask(options('general.task_name')
                                        ).setState(task.TASK_RUNNING
                                                   ).addMessage(task.MSG_SILENT, 'Starting realizing'))

    try:
        cluster = loadCluster('localhost', 'local')
        ctype = cluster.config('general.ctype')
        tf = tagfile.loadTagFile(os.path.join(cluster.config('dirs.tag_dir'), options('general.tag_name')))

        if not tagfile.hasFiles(tf) and tagfile.isPhantom(tf):
            outDir = os.path.join(cluster.config('dirs.upload_dir'), options('general.tag_name'))

            runSystemEx('mkdir -p ' + outDir)
            tagfile.realizePhantom(ctype,
                                       outDir,
                                       tf)
            tsk = tsk.progress()

            # Need to fix this so it makes use of tag_options

            metadataKeys = [k.split('.', 1)[1] for k in tf.keys() if k.startswith('metadata.')]
            metadata = dict([(k, tf('metadata.' + k)) for k in metadataKeys])                

            tagTask = tagData('localhost',
                              'local',
                              options('general.tag_name'),
                              outDir,
                              [outDir],
                              recursive=True,
                              expand=True,
                              append=False,
                              overwrite=True,
                              metadata=metadata)

            endState, tsk = task_utils.blockOnTaskAndForward('localhost',
                                                             'local',
                                                             tagTask,
                                                             tsk)
            if endState == task.TASK_FAILED:
                raise Exception('tagData call failed: ' + tagTask)
            else:
                tsk = tsk.progress().setState(task.TASK_COMPLETED)
        else:
            ##
            # Skip the two steps that happened in there
            tsk = tsk.progress(2).addMessage(task.MSG_SILENT, 'File tag already realized').setState(task.TASK_COMPLETED)

    except tagfile.MissingTagFileError, err:
        tsk = tsk.setState(task.TASK_FAILED).addException('Unable to load tagfile: ' + str(err), err, errors.getStacktrace())
        raise
        
    tsk = task.updateTask(tsk)



if __name__ == '__main__':
    runCatchError(lambda : task_utils.runTaskMain(main,
                                                  *buildConfigN(OPTIONS)),
                  mongoFail(dict(action='realizePhantom')))

#!/usr/bin/env python
##
# Uploads files to a cluster
from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.logging import errorPrint
from igs.utils import errors

from vappio.core.error_handler import runCatchError, mongoFail

from vappio.instance.transfer import downloadPipeline, DownloadPipelineOverwriteError

from vappio.webservice.cluster import loadCluster
from vappio.webservice.pipeline import pipelineStatus

from vappio.tasks import task

OPTIONS = [
    ('name', '', '--name', 'Name of cluster', notNone),
    ('task_name', '', '--task-name', 'Name of task', notNone),
    ('pipeline', '-p', '--pipeline-name', 'Name of pipeline', notNone),
    ('output_dir', '-o', '--output-dir', 'Directory the output file should go to', notNone),
    ('overwrite', '', '--overwrite', 'Do you want to overwrite a local file if it already exists?', defaultIfNone(False), True),
    ]



def main(options, _args):
    tsk = task.updateTask(task.loadTask(options('general.task_name')
                                        ).setState(task.TASK_RUNNING
                                                   ).addMessage(task.MSG_SILENT, 'Starting download'))
    
    pipelines = pipelineStatus('localhost', options('general.name'), lambda p : p.name == options('general.pipeline'))
    if not pipelines:
        raise Exception('No pipeline found by name: ' + options('general.pipeline'))

    pid = pipelines[0].pid

    cluster = loadCluster('localhost', options('general.name'))
    
    try:
        downloadPipeline(cluster.master,
                         cluster.config,
                         pid,
                         options('general.output_dir'),
                         options('general.pipeline') + '_output',
                         options('general.overwrite'),
                         log=True)
        tsk = task.updateTask(tsk.progress().setState(task.TASK_COMPLETED))
    except DownloadPipelineOverwriteError, err:
        tsk = task.updateTask(tsk.setState(task.TASK_FAILED
                                           ).addMessage(task.MSG_ERROR, 'File already exists and you have chosen not to overwrite'))
        errorPrint('')
        errorPrint('FAILING, File already exists and you have chosen not to overwrite')
        errorPrint('')
        raise
    except Exception, err:
        tsk = tsk.setState(task.TASK_FAILED).addException(str(err), err, errors.getStacktrace())        
        raise

            
if __name__ == '__main__':
    runCatchError(lambda : main(*buildConfigN(OPTIONS)),
                  mongoFail(dict(action='downloadPipelineOutput')))
    

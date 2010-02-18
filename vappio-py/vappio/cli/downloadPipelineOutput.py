#!/usr/bin/env python
##
# Uploads files to a cluster
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.ssh import scpFromEx
from igs.utils.logging import errorPrintS, errorPrint
from igs.utils.functional import compose

from vappio.instance.transfer import downloadPipeline, DownloadPipelineOverwriteError

from vappio.cluster.persist import load, dump

from vappio.pipeline_tools.utils import pipelineStatus

OPTIONS = [
    ('name', '', '--name', 'Name of cluster', notNone),
    ##
    # Want to make sure this is an int but we want it as a string later in the program
    ('pipeline', '-p', '--pipeline_name', 'Name of pipeline', notNone),
    ('output_dir', '-o', '--output_dir', 'Directory the output file should go to', notNone),
    ('overwrite', '', '--overwrite', 'Do you want to overwrite a local file if it already exists?', defaultIfNone(False), True),
    ]



def main(options, _args):
    cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))    

    pipelines = pipelineStatus(cluster, lambda p : p['name'] == options('general.pipeline'))
    if not pipelines:
        raise Exception('No pipeline found by name: ' + options('general.pipeline'))

    pid = pipelines[0]['pid']
    
    try:
        downloadPipeline(cluster.master,
                         cluster.config,
                         pid,
                         options('general.output_dir'),
                         options('general.pipeline') + '_output',
                         options('general.overwrite'),
                         log=True)
    except DownloadPipelineOverwriteError, err:
        errorPrint('')
        errorPrint('FAILING, File already exists and you have chosen not to overwrite')
        errorPrint('')
        
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

#!/usr/bin/env python
import os
import time

from igs.utils.core import getStrBetween
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery
from igs.utils.commands import runSystemEx

from vappio.tasks.utils import createTaskAndSave

class DownloadPipelineOutput(CGIPage):
    def body(self):
        request = readQuery()

        taskName = createTaskAndSave(request['name'] + '-downloadPipelineOutput-' + str(time.time()), 1)
        
        cmd = ['downloadPipelineOutputR.py',
               '--name=' + request['name'],
               '--pipeline-name=' + request['pipeline_name'],
               '--output-dir=' + request['output_dir'],
               '--task-name=' + taskName]

        if request['overwrite']:
            cmd.append('--overwrite')

        cmd.append('>> /tmp/downloadPipelineOutput.log 2>&1 &')

        runSystemEx(' '.join(cmd))

        return taskName
               

        
generatePage(DownloadPipelineOutput())

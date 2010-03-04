#!/usr/bin/env python
import os
import json

from igs.utils.core import getStrBetween
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery
from igs.utils.commands import runSystemEx


class DownloadPipelineOutput(CGIPage):
    def body(self):
        request = readQuery()

        cmd = ['downloadPipelineOutputR.py',
               '--name=' + request['name'],
               '--pipeline-name=' + request['pipeline_name'],
               '--output-dir=' + request['output_dir']]

        if request['overwrite']:
            cmd.append('--overwrite')

        cmd.append('>> /tmp/downloadPipelineOutput.log 2>&1 &')

        runSystemEx(' '.join(cmd))

        return json.dumps([True, None])
               

        
generatePage(DownloadPipelineOutput())

#!/usr/bin/env python

import cgi
import json

from twisted.python.reflect import namedModule

from igs.utils.config import configFromEnv
from igs.utils.cli import CLIError
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery

from vappio.ergatis.pipeline import runPipeline

from vappio.pipeline_tools.persist import dump

class RunPipeline(CGIPage):

    def body(self):
        request = readQuery()
        pipelineName = request['pipeline']
        conf = configFromEnv()
        
        pipeline = namedModule('vappio.pipelines.' + pipelineName)
        pipelineObj = runPipeline(request['pipeline_name'], pipeline, request['args'])
        dump(conf('env.VAPPIO_HOME'), pipelineObj)
        return json.dumps([True, pipelineObj.pid])

generatePage(RunPipeline())

#!/usr/bin/env python

import cgi
import json

from twisted.python.reflect import namedModule

from igs.utils.config import configFromEnv
from igs.utils.cli import CLIError
from igs.cgi.handler import CGIPage, generatePage

from vappio.ergatis.pipeline import runPipeline

from vappio.pipeline_tools.persist import dump

class RunPipeline(CGIPage):

    def body(self):
        form = cgi.FieldStorage()
        request = json.loads(form['request'].value)
        pipelineName = request['pipeline']
        conf = configFromEnv()
        
        try:
            pipeline = namedModule('vappio.pipelines.' + pipelineName)
            pipelineObj = runPipeline(request['pipeline_name'], pipeline, json.loads(request['args']))
            dump(conf('env.VAPPIO_HOME'), pipelineObj)
            return json.dumps([True, pipelineObj.pid])
        except CLIError, err:
            return json.dumps([False, str(err)])
        except ImportError:
            return json.dumps([False, 'The requested pipeline could not be found'])

generatePage(RunPipeline())

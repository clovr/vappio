#!/usr/bin/env python

import cgi
import json

from twisted.python.reflect import namedModule

from igs.utils.cli import CLIError
from igs.cgi.handler import CGIPage, generatePage

from vappio.ergatis.pipeline import runPipeline



class RunPipeline(CGIPage):

    def body(self):
        form = cgi.FieldStorage()
        request = json.loads(form['request'].value)
        pipelineName = request['pipeline']

        try:
            pipeline = namedModule('vappio.pipelines.' + pipelineName)
            pipelineObj = runPipeline(pipeline, json.loads(request['args']))
            return json.dumps([True, pipelineObj.pid])
        except CLIError, err:
            return json.dumps([False, str(err)])
        except ImportError:
            return json.dumps([False, 'The requested pipeline could not be found'])

generatePage(RunPipeline())

#!/usr/bin/env python

import cgi
import json

from twisted.python.reflect import namedAny, ModuleNotFound

from igs.cgi.handler import CGIPage, generatePage

class RunPipeline(CGIPage):

    def body(self):
        form = cgi.FieldStorage()
        pipelineName = form['pipeline'].value

        try:
            pipeline = namedAny('vappio.pipelines.' + pipelineName)
            pipelineId = runPipeline(pipeline, json.loads(form['args'].value))
            return json.dumps([True, pipelineId])
        except ModuleNotFound:
            return json.dumps([False, 'The requested pipeline could not be found'])

generatePage(RunPipeline())

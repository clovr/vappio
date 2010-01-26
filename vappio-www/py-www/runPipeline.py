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
        pipelineName = form['pipeline'].value

        try:
            pipeline = namedModule('vappio.pipelines.' + pipelineName)
            pipelineId = runPipeline(pipeline, json.loads(form['args'].value))
            return json.dumps([True, pipelineId])
        except CLIError, err:
            return json.dumps([False, str(err)])
        except ImportError:
            return json.dumps([False, 'The requested pipeline could not be found'])

generatePage(RunPipeline())

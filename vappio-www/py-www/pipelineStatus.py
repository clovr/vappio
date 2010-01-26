#!/usr/bin/env python
import os
import cgi
import json

from igs.utils.core import getStrBetween
from igs.utils.config import configFromEnv
from igs.cgi.handler import CGIPage, generatePage

from vappio.pipeline_tools.persist import load

def getPipelineStatus(pipeline):
    conf = configFromEnv()
    p = load(os.path.join(conf('env.VAPPIO_HOME')), pipeline)
    try:
        return [True, p.state()]
    except Exception, err:
        return [False, str(err)]

class PipelineStatus(CGIPage):

    def body(self):
        form = cgi.FieldStorage()
        pipelines = json.loads(form['pipeline'].value)

        try:
            return json.dumps([True, dict([(p, getPipelineStatus(p)) for p in pipelines])])
        except Exception, err:
            return json.dumps([False, str(err)])

generatePage(PipelineStatus())

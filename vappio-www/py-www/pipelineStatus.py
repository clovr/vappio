#!/usr/bin/env python
import os
import cgi
import json

from igs.utils.core import getStrBetween
from igs.utils.config import configFromEnv
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery

from vappio.pipeline_tools.persist import load, loadAll

def getPipelineStatus(pipeline):
    try:
        return [True, {'state': pipeline.state(), 'ptype': pipeline.ptypeStr()}]
    except Exception, err:
        return [False, str(err)]

class PipelineStatus(CGIPage):

    def body(self):
        conf = configFromEnv()
        request = readQuery()
    
        try:
            if request['pipelines']:
                pipelines = [load(conf('env.VAPPIO_HOME'), p) for p in request['pipelines']]
            else:
                pipelines = loadAll(conf('env.VAPPIO_HOME'))
        
            return json.dumps([True, dict([(p.name, getPipelineStatus(p)) for p in pipelines])])
        except Exception, err:
            return json.dumps([False, str(err)])

generatePage(PipelineStatus())

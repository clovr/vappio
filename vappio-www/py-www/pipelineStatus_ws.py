#!/usr/bin/env python
import os
import json

from igs.utils.core import getStrBetween
from igs.utils.config import configFromEnv
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery

from vappio.pipeline_tools.persist import load, loadAll

def getPipelineStatus(pipeline):
    try:
        return [True, {'name': pipeline.name,
                       'state': pipeline.state(),
                       'ptype': pipeline.ptypeStr(),
                       'pid': pipeline.pid}]
    except Exception, err:
        return [False, str(err)]

class PipelineStatus(CGIPage):

    def body(self):
        conf = configFromEnv()
        request = readQuery()
    
        if request['pipelines']:
            pipelines = [load(conf('env.VAPPIO_HOME'), p) for p in request['pipelines']]
        else:
            pipelines = loadAll(conf('env.VAPPIO_HOME'))
        
        return json.dumps([(True, getPipelineStatus(p)) for p in pipelines])
        
generatePage(PipelineStatus())

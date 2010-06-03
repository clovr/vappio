#!/usr/bin/env python
import os

from igs.utils.core import getStrBetween
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery

from vappio.pipeline_tools.persist import load, loadAll

from vappio.webservice.cluster import loadCluster

URL = '/vappio/pipelineStatus_ws.py'

def getPipelineStatus(pipeline):
    try:
        complete, total = pipeline.progress()
        return [True, {'name': pipeline.name,
                       'state': pipeline.state(),
                       'ptype': pipeline.ptypeStr(),
                       'pid': pipeline.pid,
                       'complete': complete,
                       'total': total}]
    except Exception, err:
        return [False, str(err)]
                
class PipelineStatus(CGIPage):

    def body(self):
        request = readQuery()

        if request['name'] == 'local':
            if request['pipelines']:
                pipelines = [load(p) for p in request['pipelines']]
            else:
                pipelines = loadAll()
        
            return [getPipelineStatus(p) for p in pipelines]
        else:
            ##
            # Forward the request onto the appropriate machine
            cluster = loadCluster('localhost', request['name'])
            request['name'] = 'local'
            return performQuery(cluster.master.publicDNS, URL, request)

        
generatePage(PipelineStatus())

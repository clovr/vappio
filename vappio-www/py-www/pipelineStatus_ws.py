#!/usr/bin/env python
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery

from vappio.ergatis import pipeline

from vappio.webservice.cluster import loadCluster

URL = '/vappio/pipelineStatus_ws.py'

def pipelineSnapshot(p):
    try:
        return [True, pipeline.pipelineSSToDict(pipeline.createPipelineSS(p))]
    except Exception, err:
        return [False, str(err)]
                
class PipelineStatus(CGIPage):

    def body(self):
        request = readQuery()

        if request['name'] == 'local':
            if request['pipelines']:
                pipelines = [pipeline.loadPipeline(p) for p in request['pipelines']]
            else:
                pipelines = pipeline.loadAllPipelines()
        
            return [pipelineSnapshot(p) for p in pipelines]
        else:
            ##
            # Forward the request onto the appropriate machine
            cluster = loadCluster('localhost', request['name'])
            request['name'] = 'local'
            return performQuery(cluster.master.publicDNS, URL, request)

        
generatePage(PipelineStatus())

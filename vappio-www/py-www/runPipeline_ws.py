#!/usr/bin/env python
from twisted.python.reflect import namedModule

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery

from vappio.ergatis.pipeline import runPipeline

from vappio.pipeline_tools.persist import dump

from vappio.webservice.cluster import loadCluster

URL = '/vappio/runPipeline_ws.py'

class RunPipeline(CGIPage):

    def body(self):
        request = readQuery()

        if request['name'] == 'local':
            pipelineName = request['pipeline']
        
            pipeline = namedModule('vappio.pipelines.' + pipelineName)
            pipelineObj = runPipeline(request['pipeline_name'], pipeline, request['args'])
            dump(pipelineObj)
            return pipelineObj.pid
        else:
            ##
            # Forward the request onto the appropriate machine
            cluster = loadCluster('localhost', request['name'])
            request['name'] = 'local'
            return performQuery(cluster.master.publicDNS, URL, request)

generatePage(RunPipeline())

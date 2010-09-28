#!/usr/bin/env python
from twisted.python.reflect import namedModule

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery
from igs.utils import config

from vappio.ergatis import pipeline as pl

from vappio.webservice.cluster import loadCluster
from vappio.webservice import pipeline as pipeline_ws

from vappio.tasks.utils import createTaskAndSave

from vappio.tasks import task


URL = '/vappio/runPipeline_ws.py'

class RunPipeline(CGIPage):

    def body(self):
        request = readQuery()

        matchingPipeline = pipeline_ws.pipelineStatus('localhost', 'local', lambda p: p.name == request['pipeline_name'])
        
        #
        # If this request is local and there does not exist a pipeline with the same name
        if request['name'] == 'local' and not matchingPipeline:
            ##
            # Each pipeline has a variable number of steps, so just set this to 1 and it will be fixed later
            taskName = createTaskAndSave('runPipeline', 1, 'Starting ' + request['pipeline_name'])
            task.updateTask(task.loadTask(taskName).setState(task.TASK_RUNNING))
            
            pipelineName = request['pipeline']
        
            pipeline = namedModule('vappio.pipelines.' + pipelineName)
            if 'args' in request:
                pipelineObj = pl.runPipeline(taskName, request['pipeline_name'], pipeline, request['args'])
            elif 'pipeline_config' in request:
                pipelineObj = pl.runPipelineConfig(taskName,
                                                   request['pipeline_name'],
                                                   pipeline,
                                                   config.configFromMap(request['pipeline_config'], lazy=True))
            else:
                raise Exception('Must provide args or pipeline_config')
            pl.savePipeline(pipelineObj)
            return taskName
        elif request['name'] == 'local':
            pipeline = matchingPipeline[0]
            if pipeline.state == 'running' or pipeline.state == 'complete':
                return matchingPipeline[0].taskName
            else:
                raise Exception('Currently do not handle running pipelines with the same name')
        else:
            #
            # Forward the request onto the appropriate machine
            cluster = loadCluster('localhost', request['name'])
            request['name'] = 'local'
            return performQuery(cluster.master.publicDNS, URL, request)

generatePage(RunPipeline())

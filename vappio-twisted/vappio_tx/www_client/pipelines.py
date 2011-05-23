from igs_tx.utils import http

PIPELINESTATUS_URL = '/vappio/pipelineStatus_ws.py'
RUNPIPELINE_URL = '/vappio/runPipeline_ws.py'

def pipelineStatusBy(host, clusterName, userName, criteria):
    return http.performQuery(host,
                             PIPELINESTATUS_URL,
                             dict(cluster=clusterName,
                                  user_name=userName,
                                  criteria=criteria))

def pipelineStatus(host, clusterName, userName,  pipelineName):
    return pipelineStatusBy(host, clusterName, userName, {'pipeline_name': pipelineName})

def runPipeline(host, clusterName, userName, parentPipeline, bareRun, queue, config, timeout=30, tries=4):
    return http.performQuery(host,
                             RUNPIPELINE_URL,
                             dict(cluster=clusterName,
                                  user_name=userName,
                                  parent_pipeline=parentPipeline,
                                  bare_run=bareRun,
                                  queue=queue,
                                  config=config),
                             timeout=timeout,
                             tries=tries)

def resumePipeline(host, clusterName, userName, pipelineName):
    return http.performQuery(host,
                             RESUMEPIPELINE_URL,
                             dict(cluster=clusterName,
                                  user_name=userName,
                                  pipeline_name=pipelineName))

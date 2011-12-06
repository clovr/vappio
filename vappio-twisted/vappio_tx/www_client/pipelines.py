from igs_tx.utils import http

LIST_URL = '/vappio/pipeline_list'
RUN_URL = '/vappio/pipeline_run'
RESUME_URL = '/vappio/pipeline_resume'
UPDATECONFIG_URL = '/vappio/pipeline_update'
CREATE_URL = '/vappio/pipeline_create'


def pipelineListBy(host, clusterName, userName, criteria, detail):
    return http.performQuery(host,
                             LIST_URL,
                             dict(cluster=clusterName,
                                  user_name=userName,
                                  criteria=criteria,
                                  detail=detail))

def pipelineList(host, clusterName, userName,  pipelineName, detail=False):
    return pipelineListBy(host, clusterName, userName, {'pipeline_name': pipelineName}, detail)

def runPipeline(host,
                clusterName,
                userName,
                parentPipeline,
                bareRun,
                queue,
                config,
                overwrite=False,
                timeout=30,
                tries=4):
    return http.performQuery(host,
                             RUN_URL,
                             dict(cluster=clusterName,
                                  user_name=userName,
                                  parent_pipeline=parentPipeline,
                                  bare_run=bareRun,
                                  overwrite=overwrite,
                                  queue=queue,
                                  config=config),
                             timeout=timeout,
                             tries=tries)

def resumePipeline(host, clusterName, userName, pipelineName):
    return http.performQuery(host,
                             RESUME_URL,
                             dict(cluster=clusterName,
                                  user_name=userName,
                                  pipeline_name=pipelineName))

def updateConfigPipeline(host,
                         clusterName,
                         userName,
                         criteria,
                         config):
    return http.performQuery(host,
                             UPDATECONFIG_URL,
                             dict(cluster=clusterName,
                                  user_name=userName,
                                  criteria=criteria,
                                  config=config))

def createPipeline(host,
                   clusterName,
                   userName,
                   pipelineName,
                   protocol,
                   queue,
                   config,
                   pipelineId=None,
                   taskName=None,
                   parentPipeline=None,
                   timeout=30,
                   tries=4):
    params = dict(cluster=clusterName,
                  user_name=userName,
                  pipeline_name=pipelineName,
                  protocol=protocol,
                  queue=queue,
                  config=config)

    if pipelineId is not None:
        params['pipeline_id'] = pipelineId

    if taskName is not None:
        params['task_name'] = taskName

    if parentPipeline:
        params['parent_pipeline'] = parentPipeline

    return http.performQuery(host,
                             CREATE_URL,
                             params,
                             timeout=timeout,
                             tries=tries)        

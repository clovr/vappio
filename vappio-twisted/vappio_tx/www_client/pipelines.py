from igs_tx.utils import http

LIST_URL = '/vappio/pipeline_list'
RUN_URL = '/vappio/pipeline_run'
RESUME_URL = '/vappio/pipeline_resume'

def pipelineListBy(host, clusterName, userName, criteria, detail):
    return http.performQuery(host,
                             LIST_URL,
                             dict(cluster=clusterName,
                                  user_name=userName,
                                  criteria=criteria,
                                  detail=detail))

def pipelineList(host, clusterName, userName,  pipelineName, detail=False):
    return pipelineListBy(host, clusterName, userName, {'pipeline_name': pipelineName}, detail)

def runPipeline(host, clusterName, userName, parentPipeline, bareRun, queue, config, overwrite=False, timeout=30, tries=4):
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

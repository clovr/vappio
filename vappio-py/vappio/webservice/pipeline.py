from igs.cgi.request import performQuery

from igs.utils import config

PIPELINESTATUS_URL = '/vappio/pipelineStatus_ws.py'
LISTPIPELINES_URL = '/vappio/listPipelines_ws.py'
RUNPIPELINE_URL = '/vappio/runPipeline_ws.py'
UPDATEPIPELINECONFIG_URL = '/vappio/updatePipelineConfig_ws.py'
DOWNLOADPIPELINEOUTPUT_URL = '/vappio/downloadPipelineOutput_ws.py'
RUNTASKLETS_URL = '/vappio/runTasklets_ws.py'
VALIDATEPIPELINECONFIG_URL = '/vappio/validatePipelineConfig_ws.py'

def pipelineStatus(host, cluster, pipelineName):
    return performQuery(host, PIPELINESTATUS_URL, dict(cluster=cluster,
                                                       criteria={'pipeline_name': pipelineName}))

def listPipelines(host, cluster):
    return performQuery(host, LISTPIPELINES_URL, dict(cluster=cluster))


def updatePipelineConfig(host, cluster, pipelineName, conf):
    return performQuery(host, UPDATEPIPELINECONFIG_URL, dict(cluster=cluster,
                                                             criteria={'pipeline_name': pipelineName},
                                                             config=conf))

def runPipeline(host, cluster, parentName, bareRun, conf, queue=None):
    return performQuery(host, RUNPIPELINE_URL, dict(cluster=cluster,
                                                    config=config.configToDict(conf),
                                                    parent_pipeline=parentName,
                                                    queue=queue,
                                                    bare_run=bareRun))


def validatePipelineConfig(host, cluster, conf):
    return performQuery(host, VALIDATEPIPELINECONFIG_URL, dict(cluster=cluster,
                                                               config=config.configToDict(conf)))

def downloadPipelineOutput(host, cluster, pipelineName, outputDir, overwrite):
    return performQuery(host, DOWNLOADPIPELINEOUTPUT_URL, dict(name=name,
                                                               pipeline_name=pipelineName,
                                                               output_dir=outputDir,
                                                               overwrite=overwrite))

def runTasklets(host, cluster, conf, tasklet):
    return performQuery(host, RUNTASKLETS_URL, dict(cluster=cluster,
                                                    conf=conf,
                                                    tasklet=tasklet))


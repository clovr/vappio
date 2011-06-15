from igs.cgi.request import performQuery

from igs.utils import config

LIST_URL = '/vappio/pipeline_list'
RUN_URL = '/vappio/pipeline_run'
RESUME_URL = '/vappio/pipeline_resume'
UPDATE_URL = '/vappio/pipeline_update'
DOWNLOADOUTPUT_URL = '/vappio/downloadPipelineOutput_ws.py'
RUNTASKLETS_URL = '/vappio/runTasklets_ws.py'
VALIDATE_URL = '/vappio/pipeline_validate'

def pipelineList(host, cluster, criteria, detail=False):
    return performQuery(host, LIST_URL, dict(cluster=cluster,
                                             criteria=criteria,
                                             detail=detail))

def updatePipelineConfig(host, cluster, pipelineName, conf):
    return performQuery(host, UPDATE_URL, dict(cluster=cluster,
                                               criteria={'pipeline_name': pipelineName},
                                               config=conf))

def runPipeline(host, cluster, parentName, bareRun, conf, queue=None, overwrite=False):
    return performQuery(host, RUN_URL, dict(cluster=cluster,
                                            config=config.configToDict(conf),
                                            parent_pipeline=parentName,
                                            queue=queue,
                                            bare_run=bareRun,
                                            overwrite=overwrite))

def resumePipeline(host, cluster, pipelineName):
    return performQuery(host, RESUME_URL, dict(cluster=cluster,
                                               pipeline_name=pipelineName))


def validatePipelineConfig(host, cluster, bareRun, conf):
    return performQuery(host, VALIDATE_URL, dict(cluster=cluster,
                                                 bare_run=bareRun,
                                                 config=config.configToDict(conf)))

def downloadPipelineOutput(host, cluster, pipelineName, outputDir, overwrite):
    return performQuery(host, DOWNLOADOUTPUT_URL, dict(name=name,
                                                       pipeline_name=pipelineName,
                                                       output_dir=outputDir,
                                                       overwrite=overwrite))

def runTasklets(host, cluster, conf, tasklet):
    return performQuery(host, RUNTASKLETS_URL, dict(cluster=cluster,
                                                    conf=conf,
                                                    tasklet=tasklet))

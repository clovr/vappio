from igs.cgi.request import performQuery

from igs.utils import config

from vappio.ergatis.pipeline import pipelineSSFromDict

PIPELINESTATUS_URL = '/vappio/pipelineStatus_ws.py'
RUNPIPELINE_URL = '/vappio/runPipeline_ws.py'
DOWNLOADPIPELINEOUTPUT_URL = '/vappio/downloadPipelineOutput_ws.py'
RUNMETRICS_URL = '/vappio/runMetrics_ws.py'

def pipelineStatus(host, name, pred=lambda _ : True):
    """
    name is the name of the cluster, not pipeline
    
    This performs a query to the cluster returning a list dicts containing
    pipeline status information.

    pred should be a function called on each pipeline.  If pred returns True the pipeline
    is included, otherwise it is not
    """

    ##
    # This query actually returns a list of tuples (True, PipelineInfo).  For now
    # we are ignoring the True part, although it may be used in the future
    #
    # We are also passing None for pipelines because the webservice API can take a list of pipeline
    # names to limit itself to.  We just aren't using that here right now
    return [pipelineSSFromDict(p)
            for ret, p in performQuery(host, PIPELINESTATUS_URL, dict(name=name, pipelines=None))
            if ret and pred(pipelineSSFromDict(p))]


def runPipeline(host, name, pipeline, pipelineName, args, pipelineQueue, overwrite=False):
    """
    pipeline is the type of pipeline (blastx, tblastn, ..)
    """
    return performQuery(host, RUNPIPELINE_URL, dict(name=name,
                                                    pipeline=pipeline,
                                                    pipeline_name=pipelineName,
                                                    args=args,
                                                    pipeline_queue=pipelineQueue,
                                                    overwrite=overwrite))
    

def runPipelineConfig(host, name, pipeline, pipelineName, conf, pipelineQueue, overwrite=False, rerun=False):
    """
    pipeline is the type of pipeline (blastx, tblastn, ..)
    """
    return performQuery(host, RUNPIPELINE_URL, dict(name=name,
                                                    pipeline=pipeline,
                                                    pipeline_name=pipelineName,
                                                    pipeline_config=config.configToDict(conf),
                                                    pipeline_queue=pipelineQueue,
                                                    overwrite=overwrite,
                                                    rerun=rerun))


def downloadPipelineOutput(host, name, pipelineName, outputDir, overwrite):
    return performQuery(host, DOWNLOADPIPELINEOUTPUT_URL, dict(name=name,
                                                               pipeline_name=pipelineName,
                                                               output_dir=outputDir,
                                                               overwrite=overwrite))

def runMetrics(host, name, conf, metrics):
    return performQuery(host, RUNMETRICS_URL, dict(name=name,
                                                   conf=conf,
                                                   metrics=metrics))


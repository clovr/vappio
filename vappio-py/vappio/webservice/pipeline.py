from igs.cgi.request import performQuery

from vappio.webservice.cluster import loadCluster

PIPELINESTATUS_URL = '/vappio/pipelineStatus_ws.py'
RUNPIPELINE_URL = '/vappio/runPipeline_ws.py'

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
    return [p
            for _ret, p in performQuery(host, PIPELINESTATUS_URL, dict(name=name, pipelines=None))
            if pred(p)]


def runPipeline(host, name, pipeline, pipelineName, args):
    """
    pipeline is the type of pipeline (blastx, tblastn, ..)
    """
    return performQuery(host, RUNPIPELINE_URL, dict(name=name,
                                                    pipeline=pipeline,
                                                    pipeline_name=pipelineName,
                                                    args=args))
    

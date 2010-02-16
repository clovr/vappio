##
# Little utilites for working with pipelines
from igs.cgi.request import performQuery


PIPELINESTATUS_URL = '/vappio/pipelineStatus_ws.py'


def pipelineStatus(cluster, pred=lambda _ : True):
    """
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
            for _ret, p in performQuery(cluster.master.publicDNS, PIPELINESTATUS_URL, {'pipelines': None})
            if pred(p)]

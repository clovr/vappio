from twisted.internet import defer

from igs_tx.utils import defer_pipe

from vappio_tx.internal_client import clusters as clusters_client

from vappio_tx.www_client import pipelines as pipelines_www_client

from vappio_tx.utils import queue

from vappio_tx.pipelines import pipeline_misc
from vappio_tx.pipelines import persist

from vappio_tx.tasks import tasks as tasks_tx

class Error(Exception):
    pass

class InvalidPipelineConfig(Error):
    pass

class InvalidParentPipeline(Error):
    def __init__(self, parentName):
        self.parentName = parentName

    def __str__(self):
        return 'Unknown parent pipeline: ' + self.parentName


def _determineProtocol(request):
    if request.body['bare_run']:
        return request.body['config']['pipeline.PIPELINE_TEMPLATE']
    else:
        return pipeline_misc.determineWrapper(request.state.machineconf,
                                              request.body['config']['pipeline.PIPELINE_TEMPLATE'])
    

@defer.inlineCallbacks
def handleWWWRunPipeline(request):
    """
    In the case of a pipeline we will do all the work necessary to
    run the pipeline and then setup a listener to run in the background
    tracking its progress.

    If bare_run is False then the pipeline run will actually be wrapped in
    `clovr_wrapper`.  Otherwise a pipeline of the type pipeline.PIPELINE_TEMPLATE
    is run.
    
    Input:
    { cluster: string
      user_name: string
      ?parent_pipeline: string
      ?queue: string
      ?overwrite: boolean
      bare_run: boolean
      config: { key/value }
    }
    Output:
    lite_pipeline
    """
    @defer.inlineCallbacks
    def _createPipeline(request):
        taskName = yield tasks_tx.createTaskAndSave('runPipelines', 0)

        # The name of a pipeline is being stored as a checksum.  Pipeline names
        # are arbitrary and the user will likely never know or care what it is.
        # The pipeline name still exists though because other tools will likely
        # find it useful to refer to a pipeline by a particular name, but if
        # we decide to change the pipeline name to something more meaningful they
        # won't have to chagne their code to use pipelineName instead of checksum
        protocol = _determineProtocol(request)
        
        if not request.body['bare_run']:
            request.body['config']['pipeline.PIPELINE_WRAPPER_NAME'] = request.body['config']['pipeline.PIPELINE_NAME']
            
        defer.returnValue(persist.Pipeline(pipelineId=None,
                                           pipelineName=checksum,
                                           userName=request.body['user_name'],
                                           protocol=protocol,
                                           checksum=checksum,
                                           taskName=taskName,
                                           queue=request.body.get('queue', 'pipelinewrapper.q'),
                                           children=[],
                                           config=request.body['config']))


    @defer.inlineCallbacks
    def _startRemotePipeline(request):
        cluster = yield clusters_client.loadCluster(request.body['cluster'],
                                                    request.body['user_name'])

        # Forward the request on to the remote cluster, set parent_pipeline to None
        ret = yield pipelines_www_client.runPipeline(cluster['master']['public_dns'],
                                                     'local',
                                                     request.body['user_name'],
                                                     None,
                                                     request.body['bare_run'],
                                                     request.body.get('queue', 'pipelinewrapper.q'),
                                                     request.body['config'],
                                                     request.body.get('overwrite', False))

        defer.returnValue(ret)

    
    # If the parent pipeline is set and doesn't exist, error
    if request.body.get('parent_pipeline'):
        parentPipelines = yield request.state.pipelinePersist.loadAllPipelinesBy({'pipeline_name': request.body['parent_pipeline']},
                                                                                 request.body['user_name'])
        if not parentPipelines:
            raise InvalidParentPipeline(request.body['parent_pipeline'])

        if len(parentPipelines) == 1:
            parentPipeline = parentPipelines[0]
        else:
            raise Exception('More than one possible parent pipeline choice, not sure what to do here')
    else:
        parentPipeline = None


    if request.body['cluster'] == 'local':
        checksum = pipeline_misc.checksumInput(request.body['config'])

        protocol = _determineProtocol(request)
        
        if protocol == 'clovr_batch_wrapper':
            errors = yield pipeline_misc.validateBatchPipelineConfig(request)
        else:
            errors = yield pipeline_misc.validatePipelineConfig(request)

        if errors:
            raise InvalidPipelineConfig('Configuration did not pass validation')

        request.body['config']['pipeline.PIPELINE_NAME'] = checksum
        
        try:
            # Pretty lame way to force control to the exceptional case
            # We aren't in a try block just for this line, though.  The line
            # that loads the pipeline could also fail
            if request.body.get('overwrite', False):
                raise persist.PipelineNotFoundError('flow control')
            
            existingPipeline = yield request.state.pipelinePersist.loadPipelineBy({'checksum': checksum,
                                                                                   'protocol': protocol},
                                                                                  request.body['user_name'])

            pipelineDict = yield request.state.pipelinesCache.pipelineToDict(existingPipeline)

            defer.returnValue(request.update(response=pipelineDict))
        except persist.PipelineNotFoundError:
            pipeline = yield _createPipeline(request)
            yield request.state.pipelinePersist.savePipeline(pipeline)

            # We want to do a deeper validation of the configuration and then run the pipeline.
            # Then we want to monitor it both through the ergatis observer and a timed update
            # of any children it has.
            #
            # We are going to do all this work in the background so we can exit the
            # handler.  Since incoming requests are rate-limited, we don't want to
            # block the handler for too long.  In this case we weren't pushing the
            # request and pipleine onto the queue for another handler to pick up
            # like we do in many other cases because we don't have to.  Deeper
            # validation is through a tasklet which is rate limited and submitting
            # a pipeline and monitoring it are all fairly light operations.
            d = pipeline_misc.deepValidation(request, pipeline)
            d.addCallback(lambda p : pipeline_misc.runPipeline(request, p))
            # runPipeline returns a pipeline monitor, not a pipeline
            d.addCallback(lambda pm : request.state.pipelinePersist.savePipeline(pm.pipeline).addCallback(lambda _ : pm.pipeline))
            d.addErrback(lambda f : tasks_tx.updateTask(pipeline.taskName,
                                                        lambda t : t.setState(tasks_tx.task.TASK_FAILED).addFailure(f)))


            pipelineDict = yield request.state.pipelinesCache.pipelineToDict(pipeline)

            if parentPipeline:
                parentPipeline = parentPipeline.update(children=list(set([tuple(e)
                                                                          for e in
                                                                          parentPipeline.children + [('local',
                                                                                                      pipeline.pipelineName)]])))
                yield request.state.pipelinePersist.savePipeline(parentPipeline)

            defer.returnValue(request.update(response=pipelineDict))
    else:
        pipelineDict = yield _startRemotePipeline(request)

        if parentPipeline:
            childPipeline = [(request.body['cluster'],
                              pipelineDict['pipeline_name'])]
            parentPipeline = parentPipeline.update(children=list(set([tuple(e) for e in parentPipeline.children + childPipeline])))
            yield request.state.pipelinePersist.savePipeline(parentPipeline)

        defer.returnValue(request.update(response=pipelineDict))



def subscribe(mq, state):
    processRunPipeline = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                 'user_name',
                                                                                 'bare_run',
                                                                                 'config']),
                                                               pipeline_misc.containsPipelineTemplate,
                                                               handleWWWRunPipeline]))
    queue.subscribe(mq,
                    state.conf('pipelines.run_www'),
                    state.conf('pipelines.concurrent_run'),
                    queue.wrapRequestHandler(state, processRunPipeline))

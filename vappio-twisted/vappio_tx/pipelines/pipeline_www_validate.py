from twisted.internet import defer

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.pipelines import pipeline_misc

@defer.inlineCallbacks
def handleWWWValidatePipelineConfig(request):
    """
    This is limited to simple type checks.
    
    Input:
    { cluster: string
      bare_run: boolean
      config: { key/value }
    }
    Output:
    { errors: [{ message: string, keys: [string] }]
    }
    """
    errors = yield pipeline_misc.validatePipelineConfig(request)
    defer.returnValue(request.update(response={'errors': errors}))



def subscribe(mq, state):
    processValidatePipelineConfig = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                            'bare_run',
                                                                                            'config']),
                                                                          pipeline_misc.containsPipelineTemplate,
                                                                          pipeline_misc.forwardToCluster(state.conf,
                                                                                                         state.conf('pipelines.validate_www')),
                                                                          handleWWWValidatePipelineConfig]))
    queue.subscribe(mq,
                    state.conf('pipelines.validate_www'),
                    state.conf('pipelines.concurrent_validate'),
                    queue.wrapRequestHandler(state, processValidatePipelineConfig))
    

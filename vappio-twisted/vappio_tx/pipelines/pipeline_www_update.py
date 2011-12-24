from twisted.internet import defer

from igs.utils import config

from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.pipelines import pipeline_misc

class Error(Exception):
    pass

@defer_utils.timeIt
@defer.inlineCallbacks
def handleWWWUpdatePipelineConfig(request):
    """
    Sets the config section of a pipeline exactly to what is given
    Input:
    { cluster: string
      user_name: string
      criteria: { key/valie }
      config: { key/value }
    }

    Output:
    None
    """
    pipelines = yield request.state.pipelinePersist.loadAllPipelinesBy(request.body['criteria'],
                                                                       request.body['user_name'])
    if len(pipelines) == 1:
        p = pipelines[0].update(config=config.configFromMap(request.body['config']))
        yield request.state.pipelinePersist.savePipeline(p)
    else:
        raise Error('More than one pipelines matches provided criteria: ' + repr(request.body['criteria']))

    defer.returnValue(request.update(response=None))

def subscribe(mq, state):
    processUpdatePipelineConfig = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                          'user_name',
                                                                                          'criteria',
                                                                                          'config']),
                                                                        pipeline_misc.forwardToCluster(state.conf,
                                                                                                       state.conf('pipelines.update_www')),
                                                                        handleWWWUpdatePipelineConfig]))
    queue.subscribe(mq,
                    state.conf('pipelines.update_www'),
                    state.conf('pipelines.concurrent_update'),
                    queue.wrapRequestHandler(state, processUpdatePipelineConfig))

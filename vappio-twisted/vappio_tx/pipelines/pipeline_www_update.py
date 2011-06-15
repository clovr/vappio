from twisted.internet import defer

from igs.utils import config

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.pipelines import pipeline_www_list

from vappio_tx.pipelines import pipeline_misc
from vappio_tx.pipelines import persist

class Error(Exception):
    pass


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
    pipelines = yield persist.loadAllPipelinesBy(request.body['criteria'],
                                                 request.body['user_name'])
    if len(pipelines) == 1:
        p = pipelines[0].update(config=config.configFromMap(request.body['config']))
        yield persist.savePipeline(p)
        pipelineDict = yield pipeline_www_list.pipelineToDict(request.state.machineconf,
                                                              p)
        yield request.state.pipelinesCache.save(pipelineDict)
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

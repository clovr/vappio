from twisted.internet import defer

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.pipelines import pipeline_run
from vappio_tx.pipelines import pipeline_misc

@defer.inlineCallbacks
def handleWWWResumePipeline(request):
    pipeline = yield request.state.pipelinePersist.loadPipelineBy({'pipeline_name': request.body['pipeline_name']},
                                                                  request.body['user_name'])
    yield pipeline_run.resume(pipeline)
    yield pipeline_misc.monitor_resume(request, pipeline)

    pipelineDict = yield request.state.pipelineCache.cache.query({'pipeline_name': request.body['pipeline_name'],
                                                                  'user_name': request.body['user_name']})

    defer.returnValue(request.update(response=pipelineDict))


def subscribe(mq, state):
    processResumePipeline = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                    'user_name',
                                                                                    'pipeline_name']),
                                                                  pipeline_misc.forwardToCluster(state.conf,
                                                                                                 state.conf('pipelines.resume_www')),
                                                                  handleWWWResumePipeline]))
    queue.subscribe(mq,
                    state.conf('pipelines.resume_www'),
                    state.conf('pipelines.concurrent_resume'),
                    queue.wrapRequestHandler(state, processResumePipeline))
    

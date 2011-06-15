from twisted.internet import defer

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.pipelines import pipeline_www_list

from vappio_tx.pipelines import pipeline_run
from vappio_tx.pipelines import pipeline_misc
from vappio_tx.pipelines import persist

@defer.inlineCallbacks
def handleWWWResumePipeline(request):
    pipeline = yield persist.loadPipelineBy({'pipeline_name': request.body['pipeline_name']},
                                             request.body['user_name'])
    yield pipeline_run.resume(pipeline)
    yield pipeline_misc.monitor(request, pipeline, True)

    pipelineLite = yield pipeline_www_list.pipelineToDictLite(request.state.machineconf,
                                                              pipeline)
    defer.returnValue(request.update(response=pipelineLite))


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
    

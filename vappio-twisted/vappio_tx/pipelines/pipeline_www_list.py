import os

from twisted.internet import defer

from igs.utils import functional as func

from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.pipelines import pipeline_misc


def removeDetail(p):
    p = dict(p)
    p.pop('config')
    return p


@defer.inlineCallbacks
def handleWWWPipelineList(request):
    """
    Input:
    { cluster: string
      user_name: string
      ?criteria: { key/value }
      ?detail: boolean
    }
    Output:
    pipeline
    """
    pipelinesDict = yield request.state.pipelinesCache.cache.query(func.updateDict({'user_name': request.body['user_name']},
                                                                                   request.body.get('criteria', {})))

    if not request.body.get('detail', False):
        pipelinesDict = map(removeDetail, pipelinesDict)
    
    defer.returnValue(request.update(response=pipelinesDict))

@defer.inlineCallbacks
def _monitorAnyPipelines(mq, state):
    pipelines = yield state.pipelinePersist.loadAllPipelinesByAdmin({})
    
    for p in pipelines:
        if p.pipelineId:
            yield pipeline_misc.monitorPipeline(func.Record(state=state, mq=mq),
                                                p)
        
    

def _forwardToCluster(conf, queueUrl):
    return queue.forwardRequestToCluster(conf('www.url_prefix') + '/' + os.path.basename(queueUrl))


@defer.inlineCallbacks
def subscribe(mq, state):
    yield defer_utils.tryUntil(10,
                               lambda : _monitorAnyPipelines(mq, state),
                               onFailure=defer_utils.sleep(2))
    
    processPipelineList = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                  'user_name']),
                                                                _forwardToCluster(state.conf, state.conf('pipelines.list_www')),
                                                                handleWWWPipelineList]))
    queue.subscribe(mq,
                    state.conf('pipelines.list_www'),
                    state.conf('pipelines.concurrent_list'),
                    queue.wrapRequestHandler(state, processPipelineList))


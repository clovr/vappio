import os

from twisted.internet import defer

from igs.utils import functional as func

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

class Error(Exception):
    pass

class EmptyCriteriaError(Error):
    pass    

@defer.inlineCallbacks
def handleWWWPipelineDelete(request):
    """
    Input:
    { cluster: string
      user_name: string
      criteria: { key/value }
      ?dry_run: boolean
    }
    Output:
    List of pipeline dictionaries
    """
    if not request.body['criteria']:
        raise EmptyCriteriaError()

    pipelinesDict = yield request.state.pipelinesCache.cache.query(func.updateDict({'user_name': request.body['user_name']},
                                                                                   request.body['criteria']))
    
    if not request.body.get('dry_run', False):
        for pipeline in pipelinesDict:
            yield request.state.pipelinePersist.removePipeline(pipeline['user_name'], pipeline['pipeline_name'])

    defer.returnValue(request.update(response=pipelinesDict))
    
def _forwardToCluster(conf, queueUrl):
    return queue.forwardRequestToCluster(conf('www.url_prefix') + '/' + os.path.basename(queueUrl))


def subscribe(mq, state):
    processPipelineDelete = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                    'user_name',
                                                                                    'criteria']),
                                                                  _forwardToCluster(state.conf, state.conf('pipelines.delete_www')),
                                                                  handleWWWPipelineDelete]))
    queue.subscribe(mq,
                    state.conf('pipelines.delete_www'),
                    state.conf('pipelines.concurrent_delete'),
                    queue.wrapRequestHandler(state, processPipelineDelete))


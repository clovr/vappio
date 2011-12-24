import os

from twisted.internet import defer

from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

@defer_utils.timeIt
@defer.inlineCallbacks
def handleTagList(request):
    if request.body.get('detail', False):
        tagDicts = yield request.state.tagsCache.cache.query(request.body.get('criteria', {}))
    else:
        tagDicts = yield request.state.tagsLiteCache.cache.query(request.body.get('criteria', {}))
        
    defer.returnValue(request.update(response=tagDicts))

def _forwardToCluster(conf, queueUrl):
    return queue.forwardRequestToCluster(conf('www.url_prefix') + '/' + os.path.basename(queueUrl))

def _loadAllTagsAndSubscribe(mq, state):
    processTagList = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                             'user_name']),
                                                           _forwardToCluster(state.conf,
                                                                             state.conf('tags.list_www')),
                                                           handleTagList]))
    
    queue.subscribe(mq,
                    state.conf('tags.list_www'),
                    state.conf('tags.concurrent_list'),
                    queue.wrapRequestHandler(state, processTagList))

    
def subscribe(mq, state):
    _loadAllTagsAndSubscribe(mq, state)


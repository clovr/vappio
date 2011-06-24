import time
import os

from twisted.python import log

from twisted.internet import defer
from twisted.internet import reactor

from igs.utils import functional as func
from igs.utils import config

from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.tags import persist

from vappio_tx.tasks import tasks as tasks_tx

TAGS_REFRESH_FREQUENCY = 30

def _removeDetail(tagDict):
    d = {}
    filteredMetadata = dict([(k, v)
                             for k, v in tagDict['metadata'].iteritems()
                             if k not in ['pipeline_configs']])
    d.update({'files': [],
              'metadata': filteredMetadata,
              'tag_name': tagDict['tag_name'],
              'file_count': len(tagDict['files']),
              'pipelines': [],
              'task_name': tagDict['task_name'],
              'state': tagDict['state'],
              'phantom': tagDict['phantom']})

    return d

@defer.inlineCallbacks
def tagToDict(tag):
    if tag.taskName:
       t = yield tasks_tx.loadTask(tag.taskName)
       state = t.state
    else:
       state = None

    d = {}
    d.update({'files': tag.files,
                  'metadata': tag.metadata})

    d.update({'tag_name': tag.tagName,
              'file_count': len(tag.files),
              'pipelines': [],
              'task_name': tag.taskName,
              'state': state,
              'phantom': config.configToDict(tag.phantom) if tag.phantom else None})
    
    defer.returnValue(d)

@defer.inlineCallbacks
def handleTagList(request):
    if request.body.get('detail', False):
        tagDicts = yield request.state.tagsCache.query(request.body.get('criteria', {}))
    else:
        tagDicts = yield request.state.tagsLiteCache.query(request.body.get('criteria', {}))
        
    defer.returnValue(request.update(response=tagDicts))

@defer.inlineCallbacks
def _cacheTagDicts(state):
    tagsList = yield persist.listTags(state.conf)

    tags = yield defer_utils.mapSerial(lambda tagName : persist.loadTag(state.conf, tagName),
                                       tagsList)

    tagDicts = yield defer_utils.mapSerial(lambda tag: tagToDict(tag),
                                           tags)

    tagLiteDicts = map(_removeDetail, tagDicts)
    
    yield defer_utils.mapSerial(state.tagsCache.save, tagDicts)
    yield defer_utils.mapSerial(state.tagsLiteCache.save, tagLiteDicts)
    # It turns out caching some of these tags is really expensive, so
    # rather than doing a full cache every N seconds, we are going to
    # cache them all once then track deltas in the appropriate
    # webservice
    #reactor.callLater(TAGS_REFRESH_FREQUENCY, _cacheTagDicts, state)

def _forwardToCluster(conf, queueUrl):
    return queue.forwardRequestToCluster(conf('www.url_prefix') + '/' + os.path.basename(queueUrl))

@defer.inlineCallbacks
def _loadAllTagsAndSubscribe(mq, state):
    yield _cacheTagDicts(state)
        
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


@defer.inlineCallbacks
def cacheTag(state, tag):
    tagDict = yield tagToDict(tag)
    yield state.tagsCache.save(tagDict)
    tagDictLite = _removeDetail(tagDict)
    yield state.tagsLiteCache.save(tagDictLite)

@defer.inlineCallbacks
def removeCachedTag(state, criteria):
    yield state.tagsCache.remove(criteria)
    yield state.tagsLiteCache.remove(criteria)

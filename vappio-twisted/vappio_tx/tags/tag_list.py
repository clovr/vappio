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

def handleTagList(request):
    log.msg('Begin tag_list:' + repr(request.body))

    tags = request.state.tags.values()
    
    if request.body.get('criteria', None):
        if 'tag_name' in request.body['criteria']:
            tags = [t
                    for t in tags
                    if t.tagName == request.body['criteria']['tag_name']]
        elif '$or' in request.body['criteria']:
            tagNames = set([t['tag_name'] for t in request.body['criteria']['$or']])
            tags = [t
                    for t in tags
                    if t.tagName in tagNames]

    if request.body.get('detail', False):
        tagDicts = [request.state.tagDicts[t.tagName] for t in tags]
    else:
        tagDicts = [_removeDetail(request.state.tagDicts[t.tagName]) for t in tags]
                
    log.msg('End tag_list:' + repr(request.body))
    return defer_pipe.ret(request.update(response=tagDicts))

@defer.inlineCallbacks
def _cacheTagDicts(state):
    tagDicts = yield defer_utils.mapSerial(lambda tag: tagToDict(tag),
                                           state.tags.values())

    state.tagDicts = dict([(t['tag_name'], t) for t in tagDicts])
    reactor.callLater(TAGS_REFRESH_FREQUENCY, _cacheTagDicts, state)

def _forwardToCluster(conf, queueUrl):
    return queue.forwardRequestToCluster(conf('www.url_prefix') + '/' + os.path.basename(queueUrl))

@defer.inlineCallbacks
def _loadAllTagsAndSubscribe(mq, state):
    tagsList = yield persist.listTags(state.conf)

    tags = yield defer_utils.mapSerial(lambda tagName : persist.loadTag(state.conf, tagName),
                                       tagsList)
    
    for t in tags:
        state.tags[t.tagName] = t

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

    


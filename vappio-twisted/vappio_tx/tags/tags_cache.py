from twisted.internet import defer

from igs.utils import dependency
from igs.utils import functional as func
from igs.utils import config

from igs_tx.utils import defer_work_queue

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.utils import mongo_cache

class TagsCache(dependency.Dependable):
    def __init__(self, persistManager):
        dependency.Dependable.__init__(self)
        
        self.persistManager = persistManager
        self.workQueue = defer_work_queue.DeferWorkQueue(1)

    @defer.inlineCallbacks
    def initialize(self):
        self.cache = yield mongo_cache.createCache('tags_cache',
                                                   lambda d : func.updateDict(d, {'_id': d['tag_name']}))
        self.persistManager.addDependent(self)

        # If there are a lot of tags we want to parallelize caching them
        self.workQueue.parallel = 100
        
        # Force all tags to be cached
        tags = yield self.persistManager.listTags()
        for tagName in tags:
            yield self.persistManager.loadTag(tagName)

        yield defer_work_queue.waitForCompletion(self.workQueue)

        # Now that we are done, set it back to 1
        self.workQueue.parallel = 1


    def update(self, who, aspect, value):
        if aspect == 'load':
            self.workQueue.add(self._tagToDictAndCache, aspect, value)
        elif aspect == 'save':
            self.workQueue.add(self._tagToDictAndCache, aspect, value)
        elif aspect == 'remove':
            self.workQueue.add(self.cache.remove, {'tag_name': value})
            self.changed(aspect, value)

    @defer.inlineCallbacks
    def _tagToDictAndCache(self, aspect, tag):
        if tag.taskName:
            try:
                t = yield tasks_tx.loadTask(tag.taskName)
                state = t.state
            except:
                state = None
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

        yield self.cache.save(d)
        self.changed(aspect, d)

        

class TagsLiteCache(dependency.Dependable):
    def __init__(self, tagsCache):
        dependency.Dependable.__init__(self)
        
        self.tagsCache = tagsCache
        self.workQueue = defer_work_queue.DeferWorkQueue(1)        

    @defer.inlineCallbacks
    def initialize(self):
        self.cache = yield mongo_cache.createCache('tags_lite_cache',
                                                   lambda d : func.updateDict(d, {'_id': d['tag_name']}))
        self.tagsCache.addDependent(self)
        
        # Force any already-cached values to be cached
        tags = yield self.tagsCache.cache.query({})
        for tagDict in tags:
            self.workQueue.add(self._removeDetailAndCache, 'load', tagDict)


    def update(self, who, aspect, value):
        if aspect == 'load':
            self.workQueue.add(self._removeDetailAndCache, aspect, value)
        elif aspect == 'save':
            self.workQueue.add(self._removeDetailAndCache, aspect, value)
        elif aspect == 'remove':
            self.workQueue.add(self.cache.remove, {'tag_name': value})
            self.changed(aspect, value)
            

    @defer.inlineCallbacks
    def _removeDetailAndCache(self, aspect, tagDict):
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

        yield self.cache.save(d)
        self.changed(aspect, d)
        

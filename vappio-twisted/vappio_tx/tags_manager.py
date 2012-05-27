#
# This manages tags.  The following actions are supported:
#
# tagData - Tag a dataset, overwrite or append, including metadata - async
# deleteTag - Delete a tag, this could include deleting dataset as well - async
# describeTags - Give detailed information on a provided set of tags - sync
# describeTagsLite - Give lite information on all tags in the system *debating the existence of this* - sync
# serviceStatus - Information about the service, such as tags currently being executed - sync

from twisted.internet import defer


from vappio_tx.mq import client

from vappio_tx.tags import persist
from vappio_tx.tags import tags_cache

from vappio_tx.tags import tag_mq_data
from vappio_tx.tags import tag_mq_delete
from vappio_tx.tags import tag_mq_list
from vappio_tx.tags import tag_mq_transfer
from vappio_tx.tags import tag_mq_realize_phantom

from vappio_tx.tags import tag_notify

class State:
    def __init__(self, conf):
        self.conf = conf
        self.tagPersist = persist.TagPersistManager(self.conf)
        self.tagsCache = tags_cache.TagsCache(self.tagPersist)
        self.tagsLiteCache = tags_cache.TagsLiteCache(self.tagsCache)
        self.tagNotify = None
        # We are going to want to serialize operations on tags
        self.tagLocks = {}

@defer.inlineCallbacks
def _subscribeToQueues(mq, state):
    state.tagNotify = tag_notify.TagNotify(mq, state.tagPersist)
     
    yield state.tagsCache.initialize()
    yield state.tagsLiteCache.initialize()


    
    tag_mq_data.subscribe(mq, state)
    tag_mq_delete.subscribe(mq, state)
    tag_mq_list.subscribe(mq, state)
    tag_mq_transfer.subscribe(mq, state)
    tag_mq_realize_phantom.subscribe(mq, state)
    
def makeService(conf):
    mqService = client.makeService(conf)
    mqFactory = mqService.mqFactory

    state = State(conf)

    defer.maybeDeferred(_subscribeToQueues, mqFactory, state)

    return mqService



#
# This manages tags.  The following actions are supported:
#
# tagData - Tag a dataset, overwrite or append, including metadata - async
# deleteTag - Delete a tag, this could include deleting dataset as well - async
# describeTags - Give detailed information on a provided set of tags - sync
# describeTagsLite - Give lite information on all tags in the system *debating the existence of this* - sync
# serviceStatus - Information about the service, such as tags currently being executed - sync

from twisted.internet import defer
from twisted.internet import reactor

from twisted.python import log

from igs.utils import functional as func

from vappio.tasks import task

from igs_tx.utils import defer_pipe


from vappio_tx.utils import queue
from vappio_tx.utils import core as vappio_tx_core
from vappio_tx.utils import mongo_cache

from vappio_tx.mq import client

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.tags import tag_data
from vappio_tx.tags import delete_tag
from vappio_tx.tags import tag_list
from vappio_tx.tags import transfer_tag
from vappio_tx.tags import realize_phantom

class State:
    def __init__(self, conf):
        self.conf = conf
        self.tagsCache = None
        self.tagsLiteCache = None
        # We are going to want to serialize operations on tags
        self.tagLocks = {}

@defer.inlineCallbacks
def _subscribeToQueues(mq, state):
    state.tagsCache = yield mongo_cache.createCache('tags_cache',
                                                    lambda d : func.updateDict(d, {'_id': d['tag_name']}))

    state.tagsLiteCache = yield mongo_cache.createCache('tags_lite_cache',
                                                        lambda d : func.updateDict(d, {'_id': d['tag_name']}))
    
    tag_data.subscribe(mq, state)
    delete_tag.subscribe(mq, state)
    tag_list.subscribe(mq, state)
    transfer_tag.subscribe(mq, state)
    realize_phantom.subscribe(mq, state)
    
def makeService(conf):
    mqService = client.makeService(conf)
    mqFactory = mqService.mqFactory

    state = State(conf)

    defer.maybeDeferred(_subscribeToQueues, mqFactory, state)

    return mqService



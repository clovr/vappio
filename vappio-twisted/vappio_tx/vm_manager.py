from twisted.internet import defer

from vappio_tx.mq import client

from vappio_tx.vm import vm_mq_info

class State:
    def __init__(self, conf):
        self.conf = conf
        self.releaseName = None
        self.majorVersion = None
        self.patchVersion = None
        self.patches = []
        self.vmType = None

@defer.inlineCallbacks
def _subscribeToQueues(mq, state):
    yield defer.maybeDeferred(vm_mq_info.subscribe, mq, state)
        
def makeService(conf):
    mqService = client.makeService(conf)

    mqFactory = mqService.mqFactory

    state = State(conf)

    _subscribeToQueues(mqFactory, state)
    
    return mqService

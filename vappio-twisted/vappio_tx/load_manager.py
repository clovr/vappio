#
# The load manager tries to control the amount of load on the master (so it does not get overloaded)
# by modifying various attributes, usually in the queues
from vappio_tx.mq import client

from vappio_tx.load import supervisor

class State:
    def __init__(self, conf):
        self.conf = conf
        self.hostname = None
        self.master = None


def _subscribeToQueues(mq, state):
    supervisor.subscribe(mq, state)

def makeService(conf):
    mqService = client.makeService(conf)

    mqFactory = mqService.mqFactory

    state = State(conf)

    _subscribeToQueues(mqFactory, state)
    
    return mqService

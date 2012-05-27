from vappio_tx.mq import client

from vappio_tx.tasks import task_list


class State:
    def __init__(self, conf):
        self.conf = conf

def _subscribeToQueues(mq, state):
    task_list.subscribe(mq, state)
        
def makeService(conf):
    mqService = client.makeService(conf)
    mqFactory = mqService.mqFactory

    state = State(conf)

    _subscribeToQueues(mqFactory, state)
    
    return mqService
    

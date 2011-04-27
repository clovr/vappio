import os
import json

from twisted.internet import defer
from twisted.internet import reactor

from twisted.python import log

from igs.utils import config
from igs.utils import core
from igs.utils import functional as func

from igs_tx.utils import defer_utils
from igs_tx.utils import global_state

from vappio.tasks import task

from vappio_tx.utils import queue
from vappio_tx.utils import core as vappio_tx_core

from vappio_tx.mq import client

from vappio_tx.clusters import persist

from vappio_tx.tasks import tasks as tasks_tx


def handleWWWPipelineStatus(request):
    pass


class State:
    def __init__(self, conf):
        self.conf = conf

def subscribeToQueues(mq, state):
    pass

def makeService(conf):
    mqService = client.makeService(conf)

    mqFactory = mqService.mqFactory

    # State is currently not used, but kept around for future purposes
    state = State(conf)

    subscribeToQueues(mqFactory, state)
    
    return mqService

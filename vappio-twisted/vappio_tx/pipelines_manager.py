from twisted.internet import defer

from igs.utils import config

from vappio_tx.mq import client

from vappio_tx.pipelines import pipeline_www_list
from vappio_tx.pipelines import pipeline_www_observer
from vappio_tx.pipelines import pipeline_www_validate
from vappio_tx.pipelines import pipeline_www_run
from vappio_tx.pipelines import pipeline_www_resume
from vappio_tx.pipelines import pipeline_www_update
from vappio_tx.pipelines import protocol_www_list

class State:
    def __init__(self, conf):
        self.conf = conf
        self.machineconf = config.configFromStream(open(conf('config.machine_conf')),
                                                   base=config.configFromEnv())
        self.pipelinesCache = None


@defer.inlineCallbacks
def _subscribeToQueues(mq, state):
    # Order matters here because pipeline_www_list does some caching
    # that other services need
    yield defer.maybeDeferred(pipeline_www_list.subscribe, mq, state)
    yield defer.maybeDeferred(pipeline_www_observer.subscribe, mq, state)
    yield defer.maybeDeferred(pipeline_www_validate.subscribe, mq, state)
    yield defer.maybeDeferred(pipeline_www_run.subscribe, mq, state)
    yield defer.maybeDeferred(pipeline_www_resume.subscribe, mq, state)
    yield defer.maybeDeferred(pipeline_www_update.subscribe, mq, state)
    yield defer.maybeDeferred(protocol_www_list.subscribe, mq, state)

def makeService(conf):
    mqService = client.makeService(conf)

    mqFactory = mqService.mqFactory

    # State is currently not used, but kept around for future purposes
    state = State(conf)

    _subscribeToQueues(mqFactory, state)
    
    return mqService

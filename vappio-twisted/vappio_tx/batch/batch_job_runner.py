import os
import json

from twisted.internet import defer

from igs.utils import functional as func
from igs.utils import config
from igs.utils import logging

from igs_tx.utils import defer_work_queue


from vappio_tx.batch import batch_state
from vappio_tx.pipelines import pipeline_misc

# Import wrappers
from vappio_tx.batch.wrapper import clovr_wrapper

class Error(Exception):
    pass

class InvalidWrapper(Error):
    pass

class InvalidAction(Error):
    pass

class JobFailed(Error):
    pass

class Options(func.Record):
    def __init__(self, configFile, batchFile, batchStatesFile, workflowConfig):
        func.Record.__init__(self,
                             configFile=configFile,
                             batchFile=batchFile,
                             batchStatesFile=batchStatesFile,
                             workflowConfig=workflowConfig)


class State:
    def __init__(self,
                 workflowConfig,
                 batchStatesFile,
                 wrapper,
                 batches,
                 innerPipelineConfig,
                 parentPipeline,
                 concurrentPrerun,
                 concurrentPipelines,
                 concurrentPostrun):
        self._workflowConfig = workflowConfig
        self.batchStatesFile = batchStatesFile
        self.wrapper = wrapper
        self.batchStates = batch_state.load(self.batchStatesFile)
        self.batches = batches
        self._innerPipelineConfig = innerPipelineConfig
        self._parentPipeline = parentPipeline
        self.prerunQueue = defer_work_queue.DeferWorkQueue(concurrentPrerun)
        self.pipelinesQueue = defer_work_queue.DeferWorkQueue(concurrentPipelines)
        self.postrunQueue = defer_work_queue.DeferWorkQueue(concurrentPostrun)

    def setConcurrentPrerun(self, num):
        self.prerunQueue.parallel = num

    def setConcurrentPipelines(self, num):
        self.pipelinesQueue.parallel = num

    def setConcurrentPostrun(self, num):
        self.postrunQueue.parallel = num

    def updateBatchState(self):
        logging.logPrint('Dumping states file with %d entries' % len(self.batchStates))
        return batch_state.dump(self.batchStatesFile, self.batchStates)

    def innerPipelineConfig(self):
        """Returns a copy of the innerPipelineConfig, safe to modify"""
        return dict(self._innerPipelineConfig)

    def workflowConfig(self):
        return self._workflowConfig

    def innerPipelineQueue(self):
        return 'pipeline.q'

    def parentPipeline(self):
        return self._parentPipeline

def _extractInnerPipelineConfig(batchConfig):
    batchDict = config.configToDict(batchConfig)
    innerPipelineConfigDict = dict([(k.split('.', 1)[1], v)
                                    for k, v in batchDict.iteritems()
                                    if k.startswith('batch_pipeline.')])

    for k in ['pipeline.PIPELINE_WRAPPER_NAME', 'pipeline.PIPELINE_NAME']:
        innerPipelineConfigDict[k] = batchDict[k]
        
    return innerPipelineConfigDict
    

def _validateWrapper(wrapper):
    if wrapper == 'clovr_wrapper':
        return clovr_wrapper.run
    else:
        raise InvalidWrapper(wrapper)

def _validateAction(action):
    if action in ['TAG_FILE', 'TAG_URL', 'TAG_METADATA', 'CONFIG']:
        return action
    else:
        raise InvalidAction(action)

def _interpretBatchFile(batchFile):
    batches = []
    currentBatchNum = None
    currentBatch = []
    for line in open(batchFile):
        line = line.strip()
        if not line or line[0] == '#':
            continue

        sline = line.split('\t')
        entry = {'action': _validateAction(sline[1]),
                 'key': sline[2],
                 'value': sline[3],
                 }
        
        batchNum = int(sline[0])

        if currentBatchNum is None:
            currentBatchNum = batchNum
        
        if currentBatchNum == batchNum:
            currentBatch.append(entry)
        else:
            batches.append(currentBatch)
            currentBatch = [entry]
            currentBatchNum = batchNum

    if currentBatch:
        batches.append(currentBatch)

    return batches


def _queueIncompleteWork(state):
    count = 0
    for idx, batch in enumerate(state.batches):
        if (idx not in state.batchStates or
            state.batchStates[idx]['state'] not in ['completed', 'failed']):
            state.pipelinesQueue.add(state.wrapper,
                                     state,
                                     state.batchStates.setdefault(idx, {'actions': batch, 'batch_num': idx}))
            count += 1

    state.updateBatchState()
    return count

@defer.inlineCallbacks
def run(options):
    logging.logPrint('Starting')
    
    batchConfig = config.configFromStream(open(options.configFile), lazy=True)
    machineConf = config.configFromStream(open('/tmp/machine.conf'))
    
    state = State(options.workflowConfig,
                  options.batchStatesFile,
                  _validateWrapper(pipeline_misc.determineWrapper(machineConf,
                                                                  batchConfig('batch_pipeline.pipeline.PIPELINE_TEMPLATE'))),
                  _interpretBatchFile(options.batchFile),
                  _extractInnerPipelineConfig(batchConfig),
                  batchConfig('pipeline.PIPELINE_WRAPPER_NAME'),
                  int(batchConfig('batch.options.CONCURRENT_PRERUN')),
                  int(batchConfig('batch.options.CONCURRENT_PIPELINES')),
                  int(batchConfig('batch.options.CONCURRENT_POSTRUN')))

    logging.logPrint('Queuing any incomplete work')
    queueCount = _queueIncompleteWork(state)
    logging.logPrint('Queued: %d' % queueCount)
    
    if state.pipelinesQueue.hasWork():
        yield defer_work_queue.waitForCompletion(state.pipelinesQueue)
    
    for batchState in state.batchStates.values():
        if batchState['state'] == 'failed':
            raise JobFailed()
        

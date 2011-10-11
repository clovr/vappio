import os
import hashlib

from twisted.python import log

from twisted.internet import defer

from igs.utils import logging
from igs.utils import functional as func

from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_work_queue

from vappio_tx.utils import queue

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.pipelines import pipeline_run
from vappio_tx.pipelines import protocol_format
from vappio_tx.pipelines import pipeline_validate
from vappio_tx.pipelines import pipeline_monitor

class Error(Exception):
    pass


class TaskPipeline:
    """
    Base class for classes that want to take the events from
    a pipeline monitor and push them through a task
    """
    def __init__(self, pipelinesCache, monitor):
        self.pipelinesCache = pipelinesCache
        self.monitor = monitor
        self.taskName = self.monitor.pipeline.taskName
        self.workQueue = defer_work_queue.DeferWorkQueue(1)

        self._stateActions = {'idle': lambda t : t.setState(tasks_tx.task.TASK_IDLE),
                              'running': lambda t : t.setState(tasks_tx.task.TASK_RUNNING
                                                               ).addNotification('Running pipeline'),
                              'failed': lambda t : t.setState(tasks_tx.task.TASK_FAILED),
                              'completed': lambda t : t.setState(tasks_tx.task.TASK_COMPLETED),
                              'waiting_to_restart': lambda t : t.setState(tasks_tx.task.TASK_RUNNING
                                                                          ).addNotification('Pipeline failed, waiting to restart')}

    def updateTask(self, updateFunc):
        self.workQueue.add(tasks_tx.updateTask, self.taskName, updateFunc)

    def forceRefresh(self):
        self.pipelinesCache.invalidate(self.monitor.pipeline.pipelineName,
                                       self.monitor.pipeline.userName)

    def update(self, whom, aspect, value):
        if aspect == 'state':
            self.updateTask(self._stateActions[value])
        elif aspect == 'task_count':
            self.updateTask(lambda t : t.update(numTasks=value['total'],
                                                completedTasks=value['completed']))
        elif aspect == 'step_completed':
            self.updateTask(lambda t : t.addMessage(tasks_tx.task.MSG_SILENT, 'Completed ' + value))
        elif aspect == 'messages':
            self.updateTask(lambda t : self._updateMessages(t, value))

        self.forceRefresh()

    def _updateMessages(self, task, messages):
        if task.messages:
            lastChecked = task.messages[-1]['timestamp']
        else:
            lastChecked = None

        latestMessages = [m for m in messages
                          if not lastChecked or lastChecked < m['timestamp']]
        
        return task.update(messages=task.messages + latestMessages)
            

        
class TaskResumePipeline(TaskPipeline):
    def __init__(self, pipelinePersist, monitor):
        TaskPipeline.__init__(self, pipelinePersist, monitor)

    def initialize(self):
        state = self.monitor.state()
        if state is None:
            # If there is no state then we're fine, we can add outselves as a
            # dependent and get the first update
            pass
        elif state == 'completed':
            self.updateTask(lambda t : t.setState(tasks_tx.task.TASK_COMPLETED))
        elif state in ['idle', 'failed']:
            # If we are idle or failed then set to idle.  Because this is a resume
            # we could be waiting for the next restart to happen
            self.updateTask(lambda t : t.setState(tasks_tx.task.TASK_IDLE))
        elif state in ['running', 'waiting_to_restart']:
            self.updateTask(lambda t : t.setState(tasks_tx.task.TASK_RUNNING))

        self.monitor.addDependent(self)
        self.forceRefresh()

    def release(self):
        self.monitor.removeDependent(self)

    
class TaskRunPipeline(TaskPipeline):
    def __init__(self, pipelinePersist, monitor):
        TaskPipeline.__init__(self, pipelinePersist, monitor)
    
    def initialize(self):
        state = self.monitor.state()
        if state is None:
            # If there is no state then we're fine, we can add outselves as a
            # dependent and get the first update
            pass
        else:
            self.updateTask(self._stateActions[state])
            
        self.monitor.addDependent(self)
        self.forceRefresh()

    def release(self):
        self.monitor.removeDependent(self)        
                     

def containsPipelineTemplate(request):
    if 'pipeline.PIPELINE_TEMPLATE' in request.body['config']:
        return defer_pipe.ret(request)
    else:
        raise Error('Must provide a config with pipeline.PIPELINE_TEMPLATE')

def determineWrapper(machineconf, pipelineTemplate):
    protocolConf = protocol_format.load(machineconf,
                                        pipelineTemplate)
    wrapper = [v for k, v in protocolConf if k == 'pipeline.PIPELINE_WRAPPER']

    if wrapper and wrapper[0]['default'] is None:
        return pipelineTemplate
    elif wrapper:
        return wrapper[0]['default']
    else:
        return 'clovr_wrapper'
    
def validatePipelineConfig(request):
    validateState = func.Record(conf=request.state.conf,
                                machineconf=request.state.machineconf,
                                mq=request.mq)
    protocolConf = protocol_format.load(request.state.machineconf,
                                        request.body['config']['pipeline.PIPELINE_TEMPLATE'])

    pipelienWrapper = determineWrapper(request.state.machineconf,
                                       request.body['config']['pipeline.PIPELINE_TEMPLATE'])
    
    if not request.body['bare_run']:
        protocolConf += protocol_format.load(request.state.machineconf,
                                             pipelineWrapper)
        
    protocol_format.applyProtocol(protocolConf, request.body['config'])
    return pipeline_validate.validate(validateState, protocolConf, request.body['config'])    

def checksumInput(request):
    keys = [k
            for k in request.body['config'].keys()
            if k.startswith('input.') or k.startswith('params.') or k == 'pipeline.PIPELINE_TEMPLATE']
    keys.sort()

    valuesCombined = ','.join([request.body['config'][k] for k in keys])

    return hashlib.md5(valuesCombined).hexdigest()

    
def deepValidation(request, pipeline):
    # Add stuff here
    return defer.succeed(pipeline)

@defer.inlineCallbacks
def runPipeline(request, pipeline):
    runState = func.Record(conf=request.state.conf,
                           machineconf=request.state.machineconf,
                           mq=request.mq)
    runningPipeline = yield pipeline_run.run(runState, pipeline)
    pipelineMonitor = pipeline_monitor.PipelineMonitor(request.state,
                                                       request.mq,
                                                       runningPipeline,
                                                       int(request.state.conf('pipelines.retries')))

    if request.state.pipelinesMonitor.contains(pipelineMonitor):
        oldPipelineMonitor = request.state.pipelinesMonitor.remove(pipelineMonitor)
        oldPipelineMonitor.release()
        
    yield pipelineMonitor.initialize()
    pipelineMonitor = request.state.pipelinesMonitor.add(pipelineMonitor)
    taskRunPipeline = TaskRunPipeline(request.state.pipelinesCache, pipelineMonitor)
    taskRunPipeline.initialize()
    
    defer.returnValue(pipelineMonitor)

@defer.inlineCallbacks
def resumePipeline(request, pipeline):
    runningPipeline = yield pipeline_run.resume(pipeline)
    pipelineMonitor = pipeline_monitor.PipelineMonitor(request.state,
                                                       request.mq,
                                                       runningPipeline,
                                                       int(request.state.conf('pipelines.retries')))

    if request.state.pipelinesMonitor.contains(pipelineMonitor):
        oldPipelineMonitor = request.state.pipelinesMonitor.remove(pipelineMonitor)
        oldPipelineMonitor.release()
        
    yield pipelineMonitor.initialize()
    pipelineMonitor = request.state.pipelinesMonitor.add(pipelineMonitor)
    taskResumePipeline = TaskResumePipeline(request.state.pipelinesCache, pipelineMonitor)
    taskResumePipeline.initialize()

    defer.returnValue(pipelineMonitor)

@defer.inlineCallbacks
def monitorPipeline(request, pipeline):
    pipelineMonitor = pipeline_monitor.PipelineMonitor(request.state,
                                                       request.mq,
                                                       pipeline,
                                                       int(request.state.conf('pipelines.retries')))

    if request.state.pipelinesMonitor.contains(pipelineMonitor):
        oldPipelineMonitor = request.state.pipelinesMonitor.remove(pipelineMonitor)
        oldPipelineMonitor.release()
        
    yield pipelineMonitor.initialize()
    pipelineMonitor = request.state.pipelinesMonitor.add(pipelineMonitor)
    taskResumePipeline = TaskRunPipeline(request.state.pipelinesCache, pipelineMonitor)
    taskResumePipeline.initialize()

    defer.returnValue(pipelineMonitor)
    
    
def forwardToCluster(conf, queueUrl):
    return queue.forwardRequestToCluster(conf('www.url_prefix') + '/' + os.path.basename(queueUrl))



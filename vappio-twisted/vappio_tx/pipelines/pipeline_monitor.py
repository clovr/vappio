import time

import pymongo

from xml.dom import minidom

from igs.utils import logging

from twisted.internet import threads
from twisted.internet import defer
from twisted.internet import reactor
from twisted.internet import error as twisted_error

from igs.xml import xmlquery

from igs.utils import core

from vappio.tasks import task

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.www_client import pipelines as pipelines_www
from vappio_tx.www_client import tasks as tasks_www

from vappio_tx.pipelines import pipeline_run

from vappio_tx.pipelines import persist

PIPELINE_UPDATE_FREQUENCY = 30

class Error(Exception):
    pass

def _log(p, msg):
    logging.debugPrint(lambda : 'MONITOR: ' + p.pipelineName + ' - ' + msg)

class MonitorState:
    def __init__(self, requestState, mq, pipeline, retries):
        self.requestState = requestState
        self.conf = requestState.conf
        self.machineconf = requestState.machineconf
        self.mq = mq
        self.pipeline = pipeline
        self.f = None
        self.retries = retries
        self.childrenSteps = 0
        self.childrenCompletedSteps = 0
        # We want to serialize access to the task
        self.taskLock = defer.DeferredLock()
        # We get a lot of repeated messages for some reason, so storing
        # the last message as not to post it twice
        self.lastMsg = None

        self.delayed = None

def _queueName(state):
    return '/queue/pipelines/observer/' + state.pipeline.taskName

def _try(f):
    count = 10
    while True:
        try:
            return f()
        except:
            if count > 0 :
                count -= 1
                time.sleep(1)
            else:
                raise

def _pipelineProgress(workflowXML):
    doc = _try(lambda : minidom.parse(workflowXML))
    query = [xmlquery.name('commandSetRoot'),
             [xmlquery.name('commandSet'),
              [xmlquery.name('status')]]]
    
    res = xmlquery.execQuery(query, doc)

    total = sum([int(r.childNodes[0].data) for r in res if r.localName == 'total'])
    complete = sum([int(r.childNodes[0].data) for r in res if r.localName == 'complete'])

    return (complete, total)

def _pipelineState(workflowXML):
    for _ in range(10):
        for line in open(workflowXML):
            if '<state>' in line:
                state = core.getStrBetween(line, '<state>', '</state>')
                if state in ['failed', 'error']:
                    return tasks_tx.task.TASK_FAILED
                elif state == 'running':
                    return tasks_tx.task.TASK_RUNNING
                elif state == 'complete':
                    return tasks_tx.task.TASK_COMPLETED
                else:
                    return tasks_tx.task.TASK_IDLE
        time.sleep(1)

    raise Error('Could not find state')
    
def _cancelDelayed(state):
    try:
        state.delayed.cancel()
        state.delayed = None
    except twisted_error.AlreadyCalled:
        pass

@defer.inlineCallbacks
def _sumChildrenPipelines(state, pl):
    numSteps = 0
    completedSteps = 0

    for cl, remotePipelineName in pl.children:
        try:
            localTask = yield tasks_tx.loadTask(state.pipeline.taskName)
            if localTask.messages:
                lastChecked = localTask.messages[-1]['timestamp']
            else:
                lastChecked = None

            remotePipelines = yield pipelines_www.pipelineList('localhost',
                                                               cl,
                                                               pl.userName,
                                                               remotePipelineName,
                                                               True)

            remotePipeline = remotePipelines[0]

            remoteTask = yield tasks_www.loadTask('localhost',
                                                  cl,
                                                  pl.userName,
                                                  remotePipeline['task_name'])

            numSteps += remoteTask['numTasks']
            completedSteps += remoteTask['completedTasks']

            messages = [m for m in remoteTask['messages']
                        if not lastChecked or lastChecked < m['timestamp']]

            yield state.taskLock.run(tasks_tx.updateTask,
                                     state.pipeline.taskName,
                                     lambda t : t.update(messages=t.messages + messages))

        except Exception, err:
            log.err(err)

    defer.returnValue((numSteps, completedSteps))


@defer.inlineCallbacks
def _loopUpdatePipelineChildren(state, pipelineState):
    if state.f == _waitingToRestart:
        _log(state.pipeline, 'Pipeline waiting to restart')
        if pipelineState == tasks_tx.task.TASK_FAILED:
            _log(state.pipeline, 'Pipeline waiting to restart in failed state, restarting')
            yield state.taskLock.run(tasks_tx.updateTask,
                                     state.pipeline.taskName,
                                     lambda t : t.addMessage(tasks_tx.task.MSG_NOTIFICATION,
                                                             'Restarting pipeline').setState(tasks_tx.task.TASK_IDLE))
            yield pipeline_run.resume(state.pipeline)
            state.f = _idle
            _log(state.pipeline, 'Restarted, moving to idle state')
        else:
            _log(state.pipeline, 'Pipeline waiting to restart, not in failed state, waiting longer')
            state.delayed = reactor.callLater(PIPELINE_UPDATE_FREQUENCY,
                                              _updatePipelineChildren,
                                              state)
    elif state.f == _running and pipelineState in [tasks_tx.task.TASK_FAILED, tasks_tx.task.TASK_COMPLETED]:
        _log(state.pipeline, 'Pipeline in running stated but failed or completed, unsubscribing %s' % pipelineState)
        yield state.taskLock.run(tasks_tx.updateTask,
                                 state.pipeline.taskName,
                                 lambda t : t.setState(pipelineState))
        _pipelineCompleted(state)
    elif pipelineState not in [tasks_tx.task.TASK_FAILED, tasks_tx.task.TASK_COMPLETED]:
        _log(state.pipeline, 'Looping')
        # Call ourselves again if the pipeline is not finished and the delayed call hasn't already been
        # cancelled
        state.delayed = reactor.callLater(PIPELINE_UPDATE_FREQUENCY,
                                          _updatePipelineChildren,
                                          state)
    
def _pipelineXmlPath(state):
    return state.conf('ergatis.pipeline_xml').replace('???', state.pipeline.pipelineId.replace('\n', ''))
    
@defer.inlineCallbacks
def _updatePipelineChildren(state):
    """
    Takes a pipeline and updates any children pipeline task information, putting
    it in the parents
    """
    # Load the latest version of the pipeline, someone could have added
    # children inbetween
    try:
        pl = yield state.requestState.pipelinePersist.loadPipelineBy({'task_name': state.pipeline.taskName},
                                                                     state.pipeline.userName)


        numSteps, completedSteps = yield _sumChildrenPipelines(state, pl)
        state.childrenSteps = numSteps
        state.childrenCompletedSteps = completedSteps

        pipelineXml = _pipelineXmlPath(state)
        completed, total = yield threads.deferToThread(_pipelineProgress, pipelineXml)
        
        yield state.taskLock.run(tasks_tx.updateTask,
                                 state.pipeline.taskName,
                                 lambda t : t.update(numTasks=numSteps + total,
                                                     completedTasks=completedSteps + completed))

        pipelineXml = _pipelineXmlPath(state)
        pipelineState = yield threads.deferToThread(_pipelineState, pipelineXml)

        yield _loopUpdatePipelineChildren(state, pipelineState)
    except pymongo.errors.AutoReconnect:
        _log(state.pipeline, 'Error connecting to mongo db, looping and trying again')
        state.delayed = reactor.callLater(PIPELINE_UPDATE_FREQUENCY,
                                          _updatePipelineChildren,
                                          state)
    except Exception, err:
        _log(state.pipeline, 'Got error %s, looping' % (str(err),))
        state.delayed = reactor.callLater(PIPELINE_UPDATE_FREQUENCY,
                                          _updatePipelineChildren,
                                          state)        

@defer.inlineCallbacks
def _waitForPipelineXmlRunningAndLoop(state):
    """
    Waits for a pipeline xml to come into running state then switches over to
    _updatePipelineChildren
    """
    pipelineXml = _pipelineXmlPath(state)
    pipelineState = yield threads.deferToThread(_pipelineState, pipelineXml)

    if state.f == _running and pipelineState == tasks_tx.task.TASK_RUNNING:
        _log(state.pipeline, 'Pipeline state is running and we are in state running, switching')
        yield _updatePipelineChildren(state)
    elif state.f == _running:
        _log(state.pipeline, 'State is %s or we are not _running, looping' % pipelineState)
        state.delayed = reactor.callLater(PIPELINE_UPDATE_FREQUENCY,
                                          _waitForPipelineXmlRunningAndLoop,
                                          state)
    else:
        _log(state.pipeline, 'Pipeline state is %s, state function is not _running, switching' % pipelineState)
        yield _updatePipelineChildren(state)
        
def _pipelineCompleted(state):
    state.mq.unsubscribe(_queueName(state))
        
# These are the different state functions
@defer.inlineCallbacks
def _idle(state, event):
    """
    Waiting for the pipeline to start
    """
    _log(state.pipeline, 'In idle state, got message')
    if event['event'] == 'start' and event['name'] == 'start pipeline:':
        yield state.taskLock.run(tasks_tx.updateTask,
                                 state.pipeline.taskName,
                                 lambda t : t.setState(task.TASK_RUNNING))
        state.f = _running
        _log(state.pipeline, 'Got start message, switching to running state, starting update loop')
        state.delayed = reactor.callLater(PIPELINE_UPDATE_FREQUENCY,
                                          _waitForPipelineXmlRunningAndLoop,
                                          state)
    else:
        logging.debugPrint(lambda : repr(event))

@defer.inlineCallbacks
def _running(state, event):
    """
    Pipeline is running, looking for failures or completion
    """
    _log(state.pipeline, 'In running state, got message')
    if event['event'] == 'finish' and event['retval'] and not int(event['retval']):
        _log(state.pipeline, 'Got a finish message')
        # Something has just finished successfully, read the XML to determine what
        completed, total = yield threads.deferToThread(_pipelineProgress, event['file'])

        yield state.taskLock.run(tasks_tx.updateTask,
                                 state.pipeline.taskName,
                                 lambda t : t.update(numTasks=total + state.childrenSteps,
                                                     completedTasks=completed + state.childrenCompletedSteps))
        
        if event['name'] != state.lastMsg:
            yield state.taskLock.run(tasks_tx.updateTask,
                                     state.pipeline.taskName,
                                     lambda t : t.addMessage(task.MSG_SILENT, 'Completed ' + event['name']))
            state.lastMsg = event['name']

        if event['name'] == 'start pipeline:':
            _log(state.pipeline, 'Finish message is for entire pipeline, marking complete')
            yield state.taskLock.run(tasks_tx.updateTask,
                                     state.pipeline.taskName,
                                     lambda t : t.setState(task.TASK_COMPLETED).addMessage(task.MSG_NOTIFICATION, 'Pipeline completed successfully'))
            _pipelineCompleted(state)
    elif event['retval'] and int(event['retval']):
        _log(state.pipeline, 'Got failure message')
        # Something bad has happened
        # Should we retry?
        if state.retries > 0:
            _log(state.pipeline, 'Retries left, going into waiting to restart state')
            state.retries -= 1
            yield state.taskLock.run(tasks_tx.updateTask,
                                     state.pipeline.taskName,
                                     lambda t : t.addMessage(tasks_tx.task.MSG_NOTIFICATION,
                                                             'Pipeline failed, waiting for it to finish and restarting'))
            state.f = _waitingToRestart
        else:
            def _setFailed(t):
                if t.state != task.TASK_FAILED:
                    return t.setState(task.TASK_FAILED).addMessage(task.MSG_ERROR, 'Task failed on step ' + event['name'])
                else:
                    return t
            yield state.taskLock.run(tasks_tx.updateTask,
                                     state.pipeline.taskName,
                                     _setFailed)
            state.f = _failed
            _log(state.pipeline, 'No restarts left, going into failed state')

def _waitingToRestart(state, event):
    """
    Just wait for the pipeline to finish, someone else will change our state
    """
    _log(state.pipeline, 'In waiting to restart state, got message')
    return defer.succeed(None)

def _failed(state, event):
    """
    The pipeline failed and we can't restart (either it's not a restartable error or
    we already tried and that failed), just waiting for the pipeline to finish
    """
    _log(state.pipeline, 'In failed message, got message')
    if event['event'] == 'finish' and event['name'] == 'start pipeline:':
        _log(state.pipeline, 'Message is pipeline finish, unsubscribing')
        _pipelineCompleted(state)

    return defer.succeed(None)

def _handleEventMsg(request):
    d = request.state.f(request.state, request.body)
    d.addCallback(lambda _ : request)
    return d

@defer.inlineCallbacks
def monitor_run(state):
    pipelineXml = state.conf('ergatis.pipeline_xml').replace('???', state.pipeline.pipelineId)
    pipelineState = yield threads.deferToThread(_pipelineState, pipelineXml)
    yield state.taskLock.run(tasks_tx.updateTask,
                             state.pipeline.taskName,
                             lambda t : t.setState(pipelineState))

    if pipelineState not in [tasks_tx.task.TASK_COMPLETED, tasks_tx.task.TASK_FAILED]:
        if pipelineState == tasks_tx.task.TASK_IDLE:
            state.f = _idle
            _log(state.pipeline, 'Starting monitoring, initial state is idle')
        else:
            state.f = _running
            _log(state.pipeline, 'Starting monitoring, initial state is running, xml says %s' % pipelineState)
            state.delayed = reactor.callLater(PIPELINE_UPDATE_FREQUENCY, _updatePipelineChildren, state)

        processEvent = defer_pipe.pipe([queue.keysInBody(['id',
                                                          'file',
                                                          'event',
                                                          'retval',
                                                          'props',
                                                          'host',
                                                          'time',
                                                          'name',
                                                          'message']),
                                        _handleEventMsg])
        
        queue.subscribe(state.mq,
                        _queueName(state),
                        1,
                        queue.wrapRequestHandler(state, processEvent))
            

@defer.inlineCallbacks
def monitor_resume(state):
    pipelineXml = state.conf('ergatis.pipeline_xml').replace('???', state.pipeline.pipelineId)
    pipelineState = yield threads.deferToThread(_pipelineState, pipelineXml)

    if pipelineState != tasks_tx.task.TASK_COMPLETED:
        if pipelineState in [tasks_tx.task.TASK_IDLE, tasks_tx.task.TASK_FAILED]:
            yield state.taskLock.run(tasks_tx.updateTask,
                                     state.pipeline.taskName,
                                     lambda t : t.setState(tasks_tx.task.TASK_IDLE))
            state.f = _idle
            _log(state.pipeline, 'Pipeline not completed, initial state in idle')
        else:
            yield state.taskLock.run(tasks_tx.updateTask,
                                     state.pipeline.taskName,
                                     lambda t : t.setState(tasks_tx.task.TASK_RUNNING))            
            state.f = _running
            _log(state.pipeline, 'Pipeline not complete, initial state in running, xml state is %s' % pipelineState)
            state.delayed = reactor.callLater(PIPELINE_UPDATE_FREQUENCY,
                                              _updatePipelineChildren,
                                              state)

        processEvent = defer_pipe.pipe([queue.keysInBody(['id',
                                                          'file',
                                                          'event',
                                                          'retval',
                                                          'props',
                                                          'host',
                                                          'time',
                                                          'name',
                                                          'message']),
                                        _handleEventMsg])
        
        queue.subscribe(state.mq,
                        _queueName(state),
                        1,
                        queue.wrapRequestHandler(state, processEvent))    

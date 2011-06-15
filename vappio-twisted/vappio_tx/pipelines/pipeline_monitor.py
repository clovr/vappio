import time

from xml.dom import minidom

from twisted.python import log

from twisted.internet import threads
from twisted.internet import defer
from twisted.internet import reactor

from igs.xml import xmlquery

from igs.utils import core

from vappio.tasks import task

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.www_client import pipelines as pipelines_www
from vappio_tx.www_client import tasks as tasks_www

from vappio_tx.pipelines import persist

PIPELINE_UPDATE_FREQUENCY = 30

class Error(Exception):
    pass

class MonitorState:
    def __init__(self, conf, machineconf, mq, pipeline):
        self.conf = conf
        self.machineconf = machineconf
        self.mq = mq
        self.pipeline = pipeline
        self.f = None
        self.retries = 1
        self.childrenSteps = 0
        self.childrenCompletedSteps = 0
        # We want to serialize access to the task
        self.taskLock = defer.DeferredLock()
        # We get a lot of repeated messages for some reason, so storing
        # the last message as not to post it twice
        self.lastMsg = None

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
    

@defer.inlineCallbacks
def _updatePipelineChildren(state):
    """
    Takes a pipeline and updates any children pipeline task information, putting
    it in the parents
    """
    # Load the latest version of the pipeline, someone could have added
    # children inbetween
    pl = yield persist.loadPipelineBy({'task_name': state.pipeline.taskName},
                                      state.pipeline.userName)

    numSteps = 0
    completedSteps = 0
    
    for cl, remotePipelineName in pl.children:
        try:
            localTask = yield tasks_tx.loadTask(state.pipeline.taskName)
            if localTask.messages:
                lastChecked = localTask.messages[-1]['timestamp']
            else:
                lastChecked = None

            remotePipeline = yield pipelines_www.pipelineList('localhost',
                                                              cl,
                                                              pl.userName,
                                                              remotePipelineName,
                                                              True)

            remotePipeline = remotePipeline[0]

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

    state.childrenSteps = numSteps
    state.childrenCompletedSteps = completedSteps

    try:
        if state.pipeline.pipelineId is not None:
            pipelineXml = state.conf('ergatis.pipeline_xml').replace('???', state.pipeline.pipelineId.replace('\n', ''))
            completed, total = yield threads.deferToThread(_pipelineProgress, pipelineXml)
        
            yield state.taskLock.run(tasks_tx.updateTask,
                                     state.pipeline.taskName,
                                     lambda t : t.update(numTasks=numSteps + total,
                                                         completedTasks=completedSteps + completed))
    except Exception, err:
        log.err(err)
    
    plTask = yield tasks_tx.loadTask(state.pipeline.taskName)
    if plTask.state not in [tasks_tx.task.TASK_FAILED, tasks_tx.task.TASK_COMPLETED]:
        reactor.callLater(PIPELINE_UPDATE_FREQUENCY, _updatePipelineChildren, state)

    
# These are the different state functions
@defer.inlineCallbacks
def _idle(state, event):
    """
    Waiting for the pipeline to start
    """
    if event['event'] == 'start' and event['name'] == 'start pipeline:':
        yield state.taskLock.run(tasks_tx.updateTask,
                                 state.pipeline.taskName,
                                 lambda t : t.setState(task.TASK_RUNNING))
        state.f = _running
    else:
        log.msg(repr(event))

@defer.inlineCallbacks
def _running(state, event):
    """
    Pipeline is running, looking for failures or completion
    """
    if event['event'] == 'finish' and event['retval'] and not int(event['retval']):
        # Something has just finished successfully
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
            yield state.taskLock.run(tasks_tx.updateTask,
                                     state.pipeline.taskName,
                                     lambda t : t.setState(task.TASK_COMPLETED).addMessage(task.MSG_NOTIFICATION, 'Pipeline completed successfully'))
            state.mq.unsubscribe(_queueName(state))
    elif event['retval'] and int(event['retval']):
        def _setFailed(t):
            if t.state != task.TASK_FAILED:
                return t.setState(task.TASK_FAILED).addMessage(task.MSG_ERROR, 'Task failed on step ' + event['name'])
            else:
                return t
        yield state.taskLock.run(tasks_tx.updateTask,
                                 state.pipeline.taskName,
                                 _setFailed)
        state.f = _failed

def _waitingToRestart(state, event):
    """
    Something bad has happened but the pipeline is still running,
    here we wait until it finishes then restart
    """
    pass

def _waitingForRestart(state, event):
    """
    A restart has happend, waiting for the 'start' event to come in
    in order to switch back into running state
    """
    pass

def _failed(state, event):
    """
    The pipeline failed and we can't restart (either it's not a restartable error or
    we already tried and that failed), just waiting for the pipeline to finish
    """
    if event['event'] == 'finish' and event['name'] == 'start pipeline:':
        state.mq.unsubscribe(_queueName(state))

    return defer.succeed(None)

def _handleEventMsg(request):
    d = request.state.f(request.state, request.body)
    d.addCallback(lambda _ : request)
    return d

@defer.inlineCallbacks
def monitor(state, resume=False):
    try:
        pipelineXml = state.conf('ergatis.pipeline_xml').replace('???', state.pipeline.pipelineId)
        pipelineState = yield threads.deferToThread(_pipelineState, pipelineXml)
        if not resume:
            yield state.taskLock.run(tasks_tx.updateTask,
                                     state.pipeline.taskName,
                                     lambda t : t.setState(pipelineState))
        if pipelineState != tasks_tx.task.TASK_COMPLETED:
            if pipelineState == tasks_tx.task.TASK_IDLE or resume and pipelineState == tasks_tx.task.TASK_FAILED:
                state.f = _idle
            else:
                state.f = _running
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
            reactor.callLater(PIPELINE_UPDATE_FREQUENCY, _updatePipelineChildren, state)

    except Error, err:
        log.err(err)

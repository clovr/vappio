import time

from xml.dom import minidom

from twisted.python import log

from twisted.internet import threads
from twisted.internet import defer
from twisted.internet import reactor

from igs.xml import xmlquery

from igs.utils import functional as func

from vappio.tasks import task

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.www_client import pipelines as pipelines_www
from vappio_tx.www_client import tasks as tasks_www

from vappio_tx.pipelines import persist

PIPELINE_UPDATE_FREQUENCY = 30

class MonitorState:
    def __init__(self, conf, machineconf, mq, pipeline):
        self.conf = conf
        self.machineconf = machineconf
        self.mq = mq
        self.pipeline = pipeline
        self.f = None
        self.retries = 1
        self.numSteps = 0
        self.completedSteps = 0
        # We want to serialize access to the task
        self.taskLock = defer.DeferredLock()
        # Will store the children information for tasks here
        self.childrenTasks = {}
        # We get a lot of repeated messages for some reason, so storing
        # the last message as not to post it twice
        self.lastMsg = None

def _queueName(state):
    return '/queue/pipelines/observer/' + state.pipeline.taskName

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
    
    for cl, remotePipelineName in pl.children:
        try:
            remotePipeline = yield pipelines_www.pipelineStatus('localhost',
                                                                cl,
                                                                pl.userName,
                                                                remotePipelineName)

            remoteTask = yield tasks_www.loadTask('localhost',
                                                  cl,
                                                  pl.userName,
                                                  remotePipeline['task_name'])
            
            childTaskInfo = state.childrenTasks.get((cl, remotePipelineName),
                                                    func.Record(numSteps=0,
                                                                completedSteps=0,
                                                                lastChecked=None))
            messages = [m for m in remoteTask['messages']
                        if not childTaskInfo.lastChecked or childTaskInfo.lastChecked < m['timestamp']]
            
            if childTaskInfo.numSteps != remotePipeline['num_steps']:
                stepsDiff = remotePipeline['num_steps'] - childTaskInfo.numSteps
            else:
                stepsDiff = 0

            if childTaskInfo.completedSteps != remotePipeline['num_complete']:
                completedStepsDiff = remotePipeline['num_complete'] - childTaskInfo.completedSteps
            else:
                completedStepsDiff = 0

            if stepsDiff or completedStepsDiff:
                yield state.taskLock.run(tasks_tx.updateTask,
                                         state.pipeline.taskName,
                                         lambda t : t.update(numTasks=t.numTasks + stepsDiff,
                                                             completedTasks=t.completedTasks + completedStepsDiff,
                                                             messages=t.messages + messages))
                
                state.childrenTasks[(cl, remotePipelineName)] = func.Record(numSteps=remotePipeline['num_steps'],
                                                                            completedSteps=remotePipeline['num_complete'],
                                                                            lastChecked=remoteTask['timestamp'])

        except Exception, err:
            log.err(err)

    plTask = yield tasks_tx.loadTask(state.pipeline.taskName)
    if plTask.state not in [tasks_tx.task.TASK_FAILED, tasks_tx.task.TASK_COMPLETED]:
        reactor.callLater(PIPELINE_UPDATE_FREQUENCY, _updatePipelineChildren, state)

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

        # If the number of steps in the XML file is different than our last check
        # then update the associated task with the difference
        if total != state.numSteps:
            totalDiff = total - state.numSteps
            yield state.taskLock.run(tasks_tx.updateTask,
                                     state.pipeline.taskName,
                                     lambda t : t.update(numTasks=t.numTasks + totalDiff))
            state.numSteps = total

        if completed != state.completedSteps:
            completedDiff = completed - state.completedSteps
            yield state.taskLock.run(tasks_tx.updateTask,
                                     state.pipeline.taskName,
                                     lambda t : t.update(completedTasks=t.completedTasks + completedDiff))
            state.completedSteps = completed


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

def monitor(state):
    state.f = _idle
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
    
                                                         

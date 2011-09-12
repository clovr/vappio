import time

import pymongo

from xml.dom import minidom

from twisted.python import log

from twisted.internet import threads
from twisted.internet import defer
from twisted.internet import reactor
from twisted.internet import error as twisted_error

from igs.xml import xmlquery

from igs.utils import logging
from igs.utils import core
from igs.utils import dependency

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.www_client import pipelines as pipelines_www
from vappio_tx.www_client import tasks as tasks_www

from vappio_tx.pipelines import pipeline_run

PIPELINE_UPDATE_FREQUENCY = 30

class Error(Exception):
    pass


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


class PipelineMonitor(dependency.Dependable):
    def __init__(self, requestState, mq, pipeline, retries):
        dependency.Dependable.__init__(self)
        
        self.requestState = requestState
        self.conf = requestState.conf
        self.machineconf = requestState.machineconf
        self.mq = mq
        self.pipeline = pipeline
        self.stateF = None
        self.retries = retries
        self.childrenSteps = 0
        self.childrenCompletedSteps = 0
        # We get a lot of repeated messages for some reason, so storing
        # the last message as not to post it twice
        self.lastMsg = None

        self.delayed = None
        self.delayedLock = defer.DeferredLock()
        
        self.pipelineState = None

    def _log(self, msg):
        if logging.DEBUG:
            log.msg('MONITOR: ' + self.pipeline.pipelineName + ' - ' + msg)
        #logging.debugPrint(lambda : 'MONITOR: ' + self.pipeline.pipelineName + ' - ' + msg)
        
    def _queueName(self):
        return '/queue/pipelines/observer/' + self.pipeline.taskName
        
    @defer.inlineCallbacks
    def _handleEventMessage(self, request):
        if self.stateF:
            yield defer.maybeDeferred(self.stateF, request.body)
        defer.returnValue(request)

    def _subscribe(self):
        processEvent = defer_pipe.pipe([queue.keysInBody(['id',
                                                          'file',
                                                          'event',
                                                          'retval',
                                                          'props',
                                                          'host',
                                                          'time',
                                                          'name',
                                                          'message']),
                                        self._handleEventMessage])
        
        queue.subscribe(self.mq,
                        self._queueName(),
                        1,
                        queue.wrapRequestHandler(None, processEvent))

    def _unsubscribe(self):
        self.mq.unsubscribe(self._queueName())
    
    @defer.inlineCallbacks
    def _updatePipelineState(self):
        pipelineXml = self.conf('ergatis.pipeline_xml').replace('???', self.pipeline.pipelineId)
        pipelineState = yield threads.deferToThread(_pipelineState, pipelineXml)
        if self.pipelineState != pipelineState:
            self.pipelineState = pipelineState
            self.changed('pipeline_state', self.pipelineState)

    def _pipelineXmlPath(self):
        return self.conf('ergatis.pipeline_xml').replace('???', self.pipeline.pipelineId.replace('\n', ''))

    @defer.inlineCallbacks
    def _waitForPipelineXmlRunningAndLoop(self):
        """
        Waits for a pipeline xml to come into running state then switches over to
        _updatePipelineChildren
        """
        pipelineXml = self._pipelineXmlPath()
        pipelineState = yield threads.deferToThread(_pipelineState, pipelineXml)

        if self.stateF == self.STATE_RUNNING and pipelineState == tasks_tx.task.TASK_RUNNING:
            self._log('Pipeline state is running and we are in state running, switching')
            yield self._updatePipelineChildren()
        elif self.stateF == self.STATE_RUNNING:
            self._log('State is %s or we are not _running, looping' % pipelineState)
            self.delayed = reactor.callLater(PIPELINE_UPDATE_FREQUENCY,
                                             self.delayedLock.run,
                                             self._waitForPipelineXmlRunningAndLoop)
        else:
            self._log('Pipeline state is %s, state function is not _running, switching' % pipelineState)
            yield self._updatePipelineChildren()


    @defer.inlineCallbacks
    def _sumChildrenPipelines(self, pl):
        numSteps = 0
        completedSteps = 0

        for cl, remotePipelineName in pl.children:
            try:
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
            except Exception, err:
                log.err(err)

        defer.returnValue((numSteps, completedSteps))
            
    @defer.inlineCallbacks
    def _updatePipelineChildren(self):
        """
        Takes a pipeline and updates any children pipeline task information, putting
        it in the parents
        """
        # Load the latest version of the pipeline, someone could have added
        # children inbetween
        try:
            pl = yield self.requestState.pipelinePersist.loadPipelineBy({'task_name': self.pipeline.taskName},
                                                                         self.pipeline.userName)


            numSteps, completedSteps = yield self._sumChildrenPipelines(pl)
            self.childrenSteps = numSteps
            self.childrenCompletedSteps = completedSteps

            pipelineXml = self._pipelineXmlPath()
            completed, total = yield threads.deferToThread(_pipelineProgress, pipelineXml)

            self.changed('task_count', {'completed': self.childrenCompletedSteps + completed,
                                        'total': self.childrenSteps + total})

            yield self._updatePipelineState()
            yield self._loopUpdatePipelineChildren()
        except pymongo.errors.AutoReconnect:
            self._log('Error connecting to mongo db, looping and trying again')
            self.delayed = reactor.callLater(PIPELINE_UPDATE_FREQUENCY,
                                             self.delayedLock.run,
                                             self._updatePipelineChildren)
        except Exception, err:
            self._log('Got error %s, looping' % (str(err),))
            self.delayed = reactor.callLater(PIPELINE_UPDATE_FREQUENCY,
                                             self.delayedLock.run,
                                             self._updatePipelineChildren)        
            


    @defer.inlineCallbacks
    def _loopUpdatePipelineChildren(self):
        if self.stateF == self.STATE_WAITING_TO_RESTART:
            self._log('Pipeline waiting to restart')
            if self.pipelineState == tasks_tx.task.TASK_FAILED:
                self._log('Pipeline waiting to restart in failed state, restarting')
                yield pipeline_run.resume(self.pipeline)
                self.stateF = self.STATE_IDLE
                self.changed('state', self.state())
                self._log('Restarted, moving to idle state')
            else:
                self._log('Pipeline waiting to restart, not in failed state, waiting longer')
                self.delayed = reactor.callLater(PIPELINE_UPDATE_FREQUENCY,
                                                 self.delayedLock.run,
                                                 self._updatePipelineChildren)
        elif self.stateF == self.STATE_RUNNING and self.pipelineState in [tasks_tx.task.TASK_FAILED, tasks_tx.task.TASK_COMPLETED]:
            self._log('Pipeline in running stated but failed or completed, unsubscribing %s' % pipelineState)
            self.stateF = self.STATE_COMPLETED if pipelineState == tasks_tx.task.TASK_COMPLETED else self.STATE_FAILED
            self.changed('state', self.state())
        elif self.pipelineState not in [tasks_tx.task.TASK_FAILED, tasks_tx.task.TASK_COMPLETED]:
            self._log('Looping')
            # Call ourselves again if the pipeline is not finished and the delayed call hasn't already been
            # cancelled
            self.delayed = reactor.callLater(PIPELINE_UPDATE_FREQUENCY,
                                             self.delayedLock.run,
                                             self._updatePipelineChildren)

            
    @defer.inlineCallbacks
    def initialize(self):
        yield self._updatePipelineState()

        self._log('Pipeline state : ' + self.pipelineState)
        
        if self.pipelineState == tasks_tx.task.TASK_COMPLETED:
            self.stateF = self.STATE_COMPLETED
            self.changed('state', self.state())
        elif self.pipelineState == tasks_tx.task.TASK_FAILED:
            self.stateF = self.STATE_FAILED
            self.changed('state', self.state())
        elif self.pipelineState == tasks_tx.task.TASK_IDLE:
            self.stateF = self.STATE_IDLE
            self.changed('state', self.state())
        elif self.pipelineState == tasks_tx.task.TASK_RUNNING:
            self.stateF = self.STATE_RUNNING
            self.delayed = reactor.callLater(PIPELINE_UPDATE_FREQUENCY,
                                             self.delayedLock.run,
                                             self._updatePipelineChildren)
            self.changed('state', self.state())

        self._subscribe()


    def release(self):
        if self.delayed:
            self.delayedLock.run(self.delayed.cancel)
        self._unsubscribe()

    def state(self):
        return {self.STATE_COMPLETED: 'completed',
                self.STATE_IDLE: 'idle',
                self.STATE_FAILED: 'failed',
                self.STATE_RUNNING: 'running',
                self.STATE_WAITING_TO_RESTART: 'waiting_to_restart',
                None: None}[self.stateF]

    def STATE_IDLE(self, event):
        self._log('In idle state, got message')
        if event['event'] == 'start' and event['name'] == 'start pipeline:':
            self.stateF = self.STATE_RUNNING
            self.changed('state', self.state())
            
            self._log('Got start message, switching to running state, starting update loop')
            self.delayed = reactor.callLater(PIPELINE_UPDATE_FREQUENCY,
                                             self.delayedLock.run,
                                             self._waitForPipelineXmlRunningAndLoop)
        else:
            logging.debugPrint(lambda : repr(event))

    @defer.inlineCallbacks
    def STATE_RUNNING(self, event):
        self._log('In running state, got message')
        if event['event'] == 'finish' and event['retval'] and not int(event['retval']):
            self._log('Got a finish message')
            # Something has just finished successfully, read the XML to determine what
            completed, total = yield threads.deferToThread(_pipelineProgress, event['file'])

            self.changed('task_count', {'completed': completed + self.childrenCompletedSteps,
                                        'total': total + self.childrenSteps})

            if event['name'] != self.lastMsg:
                self.changed('step_completed', event['name'])
                self.lastMsg = event['name']

            if event['name'] == 'start pipeline:':
                self._log('Finish message is for entire pipeline, marking complete')
                self.stateF = self.STATE_COMPLETED
                self.changed('state', self.state())

        elif event['retval'] and int(event['retval']):
            self._log('Got failure message')
            # Something bad has happened
            # Should we retry?
            if self.retries > 0:
                self._log('Retries left, going into waiting to restart state')
                self.retries -= 1
                self.stateF = self.STATE_WAITING_TO_RESTART
                self.changed('state', self.state())
            else:
                self.stateF = self.STATE_FAILED
                self.changed('state', self.state())
                self._log('No restarts left, going into failed state')
        
    def STATE_WAITING_TO_RESTART(self, event):
        self._log('In waiting to restart, got message')


    def STATE_COMPLETED(self, event):
        self._log('In completed, got message')
        
    def STATE_FAILED(self, event):
        self._log('In failed message, got message')
        if event['event'] == 'finish' and event['name'] == 'start pipeline:':
            self._log('Message is pipeline finish')


class PipelineMonitorManager:
    def __init__(self):
        self.monitors = {}

    def add(self, monitor):
        """
        Adds a monitor to the group being managed.  If a monitor for this
        pipeline already exists then it is replaced, if it does not it is
        added
        """
        self.monitors[(monitor.pipeline.pipelineName, monitor.pipeline.userName)] = monitor
        return monitor

    def remove(self, monitor):
        """
        Remove a specified monitor, if it exists.  The monitor is returned regardless.
        """
        return self.monitors.pop((monitor.pipeline.pipelineName, monitor.pipeline.userName), monitor)

    def contains(self, monitor):
        return monitor.pipeline.pipelineName in self.monitors

    def findMonitor(self, pipelineName, userName):
        """
        Tries to locate a pipeline monitor by a pipeline name and user name. Returns None on failure.
        """
        return self.monitors.get((pipelineName, userName), None)
    

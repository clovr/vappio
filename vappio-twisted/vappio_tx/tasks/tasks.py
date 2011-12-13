#
# Twisted-ized version of the task functions
import time

from twisted.internet import threads
from twisted.internet import defer

from igs.utils import logging

from vappio.tasks import task
from vappio.tasks import utils as task_utils

from igs_tx.utils import defer_utils

from vappio_tx.www_client import tasks as tasks_client

def createTaskAndSave(tType, numTasks, initialMsg=None):
    return threads.deferToThread(task_utils.createTaskAndSave, tType, numTasks, initialMsg)

def updateTask(taskName, f):
    d = threads.deferToThread(task.loadTask, taskName)
    d.addCallback(f)
    d.addCallback(lambda t : threads.deferToThread(task.updateTask, t))
    return d

def loadTask(taskName):
    return threads.deferToThread(task.loadTask, taskName)

@defer.inlineCallbacks
def blockOnTask(host, cluster, taskName, notifyF=logging.logPrint, errorF=logging.errorPrint):
    endStates = [task.TASK_FAILED, task.TASK_COMPLETED]
    state = None
    prevTime = None
    sleepTime = 1
    yield defer_utils.sleep(sleepTime)()
    while state not in endStates:
        tsk = yield tasks_client.loadTask(host, cluster, 'guest', taskName)
        tsk = task.taskFromDict(tsk)
        state = tsk.state
        if prevTime is None:
            msgs = tsk.getMessages()
        else:
            msgs = tsk.getMessagesAfterTime(prevTime)
        prevTime = tsk.timestamp
        for m in msgs:
            if m['mtype'] == task.MSG_ERROR:
                errorF(m['text'])
            elif m['mtype'] == task.MSG_NOTIFICATION:
                notifyF(m['text'])
            elif logging.DEBUG and m['mtype'] == task.MSG_SILENT:
                logging.debugPrint(lambda : m['text'])
        ##
        # Make this configurable
        if state not in endStates:
            sleepTime = sleepTime < 30 and sleepTime * 2 or 30
            yield defer_utils.sleep(sleepTime)()

    defer.returnValue(state)

def blockOnTaskAndForward(host, cluster, taskName, dstTask):
    d = threads.deferToThread(task_utils.blockOnTaskAndForward, host, cluster, taskName, dstTask)
    return d

def setRequestComplete(request):
    d = updateTask(request.body['task_name'],
                    lambda t : t.setState(task.TASK_COMPLETED))
    d.addCallback(lambda _ : request)
    return d

def setRequestFailed(f, request):
    d = updateTask(request.body['task_name'],
                   lambda t : t.setState(task.TASK_FAILED).addFailure(f))
    d.addCallback(lambda _ : request)
    return d

#
# Twisted-ized version of the task functions
from twisted.internet import threads

from igs.utils import logging

from vappio.tasks import task
from vappio.tasks import utils as task_utils

def createTaskAndSave(tType, numTasks, initialMsg=None):
    return threads.deferToThread(task_utils.createTaskAndSave, tType, numTasks, initialMsg)

def updateTask(taskName, f):
    d = threads.deferToThread(task.loadTask, taskName)
    d.addCallback(f)
    d.addCallback(lambda t : threads.deferToThread(task.updateTask, t))
    return d

def loadTask(taskName):
    return threads.deferToThread(task.loadTask, taskName)

def blockOnTask(host, cluster, taskName, notifyF=logging.logPrint, errorF=logging.errorPrint):
    d = threads.deferToThread(task_utils.blockOnTask, host, cluster, taskName, notifyF, errorF)
    return d

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

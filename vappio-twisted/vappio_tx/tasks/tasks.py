#
# Twisted-ized version of the task functions
from twisted.internet import threads

from vappio.tasks import task
from vappio.tasks import utils as task_utils

def createTaskAndSave(tType, numTasks, initialMsg=None):
    return threads.deferToThread(task_utils.createTaskAndSave, tType, numTasks, initialMsg)


def updateTask(taskName, f):
    d = threads.deferToThread(task.loadTask, taskName)
    d.addCallback(f)
    d.addCallback(lambda t : threads.deferToThread(task.updateTask, t))
    return d


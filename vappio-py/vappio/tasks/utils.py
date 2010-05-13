import time

from igs.utils.logging import logPrint, errorPrint, debugPrint
from igs.utils import logging

from vappio.webservice.task import loadTask

from vappio.tasks import task

def blockOnTask(host, name, taskName, notifyF=logPrint, errorF=errorPrint):
    endStates = [task.TASK_FAILED, task.TASK_COMPLETED]
    state = None
    ##
    # Some tasks finish *really* quick but this executes just a bit faster.
    # so wait 2 seconds before checking so we don't end up waitign 30
    # seconds for no good reason
    time.sleep(2)
    while state not in endStates:
        tsk = loadTask(host, name, taskName, read=True)
        state = tsk.state
        for m in tsk.getUnreadMessages():
            if m['mtype'] == task.MSG_ERROR:
                errorF(m['data'])
            elif m['mtype'] == task.MSG_NOTIFICATION:
                notifyF(m['data'])
            elif logging.DEBUG and m['mtype'] == task.MSG_SILENT:
                debugPrint(lambda : m['data'])
        ##
        # Make this configurable
        if state not in endStates:
            time.sleep(30)

    return state


def blockOnTaskAndForward(host, name, taskName, dstTask):
    notifications = []
    errors = []
    endState = blockOnTask(host,
                           name,
                           taskName,
                           notifyF=notifications.append,
                           errorF=errors.append)
    for m in notifications:
        dstTask = dstTask.addMessage(task.MSG_NOTIFICATION, m)
    for m in errors:
        dstTask = dstTask.addMessage(task.MSG_ERROR, m)
        
    tsk = task.updateTask(dstTask)

    return endState, tsk


def createTaskAndSave(name, numTasks):
    """
    This creates a task and saves it immediatly with an IDLE state
    and returns the name of it
    """
    tsk = task.createTask(name, task.TASK_IDLE, numTasks)
    task.saveTask(tsk)
    return name

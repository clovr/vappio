import time

from igs.utils.logging import logPrint, errorPrint, debugPrint
from igs.utils import logging
from igs.utils import errors

from vappio.webservice.task import loadTask

from vappio.tasks import task

def blockOnTask(host, name, taskName, notifyF=logPrint, errorF=errorPrint):
    endStates = [task.TASK_FAILED, task.TASK_COMPLETED]
    state = None
    prevTime = None
    ##
    # Some tasks finish *really* quick but this executes just a bit faster.
    # so wait 2 seconds before checking so we don't end up waitign 30
    # seconds for no good reason
    time.sleep(2)
    while state not in endStates:
        tsk = loadTask(host, name, taskName)
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
                debugPrint(lambda : m['text'])
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


def createTaskAndSave(tType, numTasks, initialMsg=None):
    """
    This creates a task and saves it immediatly with an IDLE state
    and returns the name of it

    tType - the type of task it is (generally corresponds to the name the task was started as)
    """
    name = tType + '-' + str(time.time())
    tsk = task.createTask(name, tType, task.TASK_IDLE, numTasks)
    if initialMsg is not None:
        tsk = tsk.addMessage(task.MSG_NOTIFICATION, initialMsg)
    task.saveTask(tsk)
    return name


def runTask(taskName, f):
    """
    This takes a task name and a function. It runs the function, if the function does not throw an exception
    then it loads the task and marks it as completed.  If an exception is thrown it loads the task and
    marks it as failed and logs the exception in the task.

    runTask will fail if the task does not exist
    """

    try:
        f()
    except Exception, err:
        task.updateTask(task.loadTask(tastkName
                                      ).setState(task.TASK_FAILED
                                                 ).addException(str(err), err, errors.getStackTrace()))

    task.updateTask(task.loadTask(taskName).setState(task.TASK_COMPLETED))
    
        
def runTaskMain(options, args, func, optionsTaskName='general.task_name'):
    """
    This is a little cheat function to wrap up running a task around what
    a standard main function looks like
    """
    return runTask(o(optionsTaskName), lambda : func(o, a))

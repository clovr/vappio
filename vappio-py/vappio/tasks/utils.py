import time

from igs.utils.logging import logPrint, errorPrint, debugPrint
from igs.utils import logging
from igs.utils import errors
from igs.utils import commands

from vappio.webservice.task import loadTask

from vappio.tasks import task

def blockOnTask(host, name, taskName, notifyF=logPrint, errorF=errorPrint):
    endStates = [task.TASK_FAILED, task.TASK_COMPLETED]
    state = None
    prevTime = None
    sleepTime = 1
    time.sleep(sleepTime)
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
            sleepTime = sleepTime < 30 and sleepTime * 2 or 30
            time.sleep(sleepTime)

    return state


def blockOnTaskAndForward(host, name, taskName, dstTask):
    notificationsL = []
    errorsL = []
    endState = blockOnTask(host,
                           name,
                           taskName,
                           notifyF=notificationsL.append,
                           errorF=errorsL.append)
    for m in notificationsL:
        dstTask = dstTask.addMessage(task.MSG_NOTIFICATION, m)
    for m in errorsL:
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
        task.updateTask(task.loadTask(taskName).setState(task.TASK_COMPLETED))
    except Exception, err:
        task.updateTask(task.loadTask(taskName
                                      ).setState(task.TASK_FAILED
                                                 ).addException(str(err), err, errors.getStacktrace()))
    
        
def runTaskMain(func, options, args, optionsTaskName='general.task_name'):
    """
    This is a little cheat function to wrap up running a task around what
    a standard main function looks like
    """
    return runTask(options(optionsTaskName), lambda : func(options, args))

def runTaskStatus(taskName, clusterName=None):
    """
    This is a simple function that takes a taskname and simply runs vp-describe-task
    on it.  It is meant to be used in specific situations in front ends.  It is not
    meant to be a generic function.  There are no guarantees that this funciton will
    exist tomorrow and it could be moved into a more fitting location at any point
    """
    cmd = ['vp-describe-task',
           '--show',
           '--show-error',
           '--exit-code',
           '--block',
           '--no-print-polling']
    if clusterName:
        cmd.append('--name=' + clusterName)
        
    cmd.append(taskName)
    
    commands.runSystemEx(' '.join(cmd))
    

##
# Currently this isn't concurrency safe, assuming that we will be such low traffic it won't be an issue though
from igs.utils.functional import Record, updateDict

from vappio.tasks.persist import load, dump


TASK_IDLE = 'idle'
TASK_RUNNING = 'running'
TASK_COMPLETED = 'completed'
TASK_FAILED = 'failed'


MSG_ERROR = 'error'
MSG_NOTIFICATION = 'notification'
##
# silent messages are for debugging purposes
MSG_SILENT = 'silent'


def taskToDict(task):
    return dict(name=task.name,
                state=task.state,
                currTask=task.currTask,
                numTasks=task.numTasks,
                messages=task.messages)

def dictToTask(d):
    return Record(name=d['name'],
                  state=d['state'],
                  currTask=d['currTask'],
                  numTasks=d['numTasks'],
                  messages=d['messages'])


def loadTask(name):
    return dictToTask(load(name))

def saveTask(task):
    return dump(taskToDict(task))

def createTask(name, state, numTasks):
    return Record(name=name,
                  state=state,
                  currTask=1,
                  numTasks=numTasks,
                  messages=[])


def addMessage(task, mtype, msg):
    return task.update(messages=task.messages + dict(mtype=mtype, data=msg, read=False))

def readMessages(task):
    """
    Returns a new task with all of the messages read
    """
    return task.update(messages=[updateDict(dict(read=True), m) for m in task.messages])

def getUnreadMessages(task):
    return [m for m in task.messages if not m['read']]

def progress(task, inc=1):
    return task.update(currTask=task.currTask + inc)

def setState(task, state):
    return task.update(state=state)


                                                     

##
# Currently this isn't concurrency safe, assuming that we will be such low traffic it won't be an issue though
from igs.utils.functional import Record


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
                currTask=task.currTask
                numTasks=task.numTasks,
                messages=task.messages)

def dictToTask(d):
    ##
    # We are just going to
    # construct the record straight
    # from the dict rather than being
    # picky about what is actually in it.
    # Hopfully it represents a valid dict
    return Record(**d)


def loadTask(name):
    return dictToTask(load(name))

def saveTask(task):
    return save(taskToDict(task))

def createTask(name, state, numTasks):
    return Record(name=name,
                  state=state,
                  currTask=1,
                  numTasks=numTasks,
                  messages=[])


def addMessage(task, mtype, msg):
    return task.update(messages=task.messages + dict(mtype=mtype, data=msg, read=False))

def progress(task, inc=1):
    return task.update(currTask=task.currTask + inc)

def setState(task, state):
    return task.update(state=state)


                                                     

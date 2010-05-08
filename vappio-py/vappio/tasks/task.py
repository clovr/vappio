##
# Currently this isn't concurrency safe, assuming that we will be such low traffic it won't be an issue though
from igs.utils.functional import Record, updateDict

from vappio.tasks.persist import load, dump, TaskDoesNotExistError


TASK_IDLE = 'idle'
TASK_RUNNING = 'running'
TASK_COMPLETED = 'completed'
TASK_FAILED = 'failed'


MSG_ERROR = 'error'
MSG_NOTIFICATION = 'notification'
##
# silent messages are for debugging purposes
MSG_SILENT = 'silent'


class Task(Record):
    def addMessage(self, mtype, msg):
        return self.update(messages=self.messages + [dict(mtype=mtype, data=msg, read=False)])

    def readMessages(self):
        """
        Returns a new self with all of the messages read
        """
        return self.update(messages=[updateDict(dict(m), dict(read=True)) for m in self.messages])

    def getUnreadMessages(self):
        return [m for m in self.messages if not m['read']]
    
    def progress(self, inc=1):
        return self.update(completedSelfs=self.completedTaskss + inc)

    def setState(self, state):
        return self.update(state=state)
    

def taskToDict(task):
    return dict(name=task.name,
                state=task.state,
                completedTasks=task.completedTasks,
                numTasks=task.numTasks,
                messages=task.messages)

def taskFromDict(d):
    return Task(name=d['name'],
                state=d['state'],
                completedTasks=d['completedTasks'],
                numTasks=d['numTasks'],
                messages=d['messages'])


def loadTask(name):
    return taskFromDict(load(name))

def saveTask(task):
    dump(taskToDict(task))
    return task

def updateTask(task):
    """
    This saves a task.  It needs to do a little bit of work in terms
    of the messages.  Because they can be read elsewhere it will load
    the task from the database (if present) and check to see if any messages
    have been marked as read.  If so it will mark its versions as read then
    save them
    """
    try:
        oldTask = loadTask(task.name)
        if len(oldTask.messages) < len(task.messages):
            task = task.update(messages=oldTask.messages + task.messages[len(oldTask.messages):])
        else:
            task = task.update(messages=oldTask.messages)
        dump(taskToDict(task))
        return task
    except TaskDoesNotExistError:
        ##
        # If this is the first time saving it won't exist, so just save it
        dump(taskToDict(task))
        return task


def createTask(name, state, numTasks):
    return Task(name=name,
                state=state,
                completedTasks=0,
                numTasks=numTasks,
                messages=[])




                                                     

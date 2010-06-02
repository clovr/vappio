##
# Currently this isn't concurrency safe, assuming that we will be such low traffic it won't be an issue though
import time

from igs.utils.functional import Record, updateDict

from vappio.tasks.persist import load, loadAll, dump, TaskDoesNotExistError


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
        t = time.time()
        return self.update(timestamp=t,
                           messages=self.messages + [dict(mtype=mtype, data=msg, timestamp=t)])

    def getMessages(self):
        return self.messages
    
    def getMessagesAfterTime(self, t):
        """
        Returns a list of message from after the specified time
        """
        return [m for m in self.messages if m['timestamp'] > t]
    
    def progress(self, inc=1):
        return self.update(timestamp=time.time(),
                           completedTasks=self.completedTasks + inc)

    def setState(self, state):
        return self.update(timestamp=time.time(),
                           state=state)
    

def taskToDict(task):
    return dict(name=task.name,
                state=task.state,
                completedTasks=task.completedTasks,
                numTasks=task.numTasks,
                messages=task.messages,
                timestamp=task.timestamp)

def taskFromDict(d):
    return Task(name=d['name'],
                state=d['state'],
                completedTasks=d['completedTasks'],
                numTasks=d['numTasks'],
                messages=d['messages'],
                timestamp=d['timestamp'])


def loadTask(name):
    return taskFromDict(load(name))

def loadAllTasks():
    return [taskFromDict(t) for t in loadAll()]

def saveTask(task):
    dump(taskToDict(task))
    return task

def updateTask(task):
    """
    Currently this does the samet hign as saveTask.  In the future this should be
    modified to ensure that the task has not been modified between load and update
    """
    return saveTask(task)



def createTask(name, state, numTasks):
    return Task(name=name,
                state=state,
                completedTasks=0,
                numTasks=numTasks,
                messages=[],
                timestamp=time.time())




                                                     

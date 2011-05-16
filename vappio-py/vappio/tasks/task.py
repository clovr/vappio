##
# Currently this isn't concurrency safe, assuming that we will be such low traffic it won't be an issue though
import time

from twisted.python import reflect

from igs.utils.functional import Record, updateDict

from vappio.tasks.persist import load, loadAll, dump, TaskDoesNotExistError

from igs_tx.utils import errors

TASK_IDLE = 'idle'
TASK_RUNNING = 'running'
TASK_COMPLETED = 'completed'
TASK_FAILED = 'failed'


MSG_ERROR = 'error'
MSG_NOTIFICATION = 'notification'
MSG_RESULT = 'result'
##
# silent messages are for debugging purposes
MSG_SILENT = 'silent'


class Task(Record):
    def __init__(self,
                 name,
                 tType,
                 state,
                 completedTasks,
                 numTasks,
                 messages,
                 timestamp):
        Record.__init__(self,
                        name=name,
                        tType=tType,
                        state=state,
                        completedTasks=completedTasks,
                        numTasks=numTasks,
                        messages=messages,
                        timestamp=timestamp)
        
    def addMessage(self, mtype, msg):
        t = time.time()
        return self.update(timestamp=t,
                           messages=self.messages + [dict(mtype=mtype, text=msg, timestamp=t)])

    def addException(self, msg, exc, stacktrace):
        t = time.time()
        return self.update(timestamp=t,
                           messages=self.messages + [dict(mtype=MSG_ERROR,
                                                          text=msg,
                                                          name=reflect.fullyQualifiedName(reflect.getClass(exc)),
                                                          stacktrace=stacktrace,
                                                          timestamp=t)])

    def addFailure(self, failure):
        t = time.time()
        return self.update(timestamp=t,
                           messages=self.messages + [dict(mtype=MSG_ERROR,
                                                          text=failure.getErrorMessage(),
                                                          name='',
                                                          stacktrace=errors.stackTraceToString(failure),
                                                          timestamp=t)])
        
        
    def addNotification(self, msg):
        return self.addMessage(MSG_NOTIFICATION, msg)

    def addResult(self, result):
        """
        Adds some kind of result to the task that can be pulled out
        """
        t = time.time()
        return self.update(timestamp=t,
                           messages=self.messages + [dict(mtype=MSG_RESULT,
                                                          result=result,
                                                          timestamp=t)])

    def getResults(self):
        return [m for m in self.messages if m['mtype'] == MSG_RESULT]
    
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
                tType=task.tType,
                state=task.state,
                completedTasks=task.completedTasks,
                numTasks=task.numTasks,
                messages=task.messages,
                timestamp=task.timestamp)

def taskFromDict(d):
    return Task(name=d['name'],
                tType=d['tType'],
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



def createTask(name, tType, state, numTasks):
    return Task(name=name,
                tType=tType,
                state=state,
                completedTasks=0,
                numTasks=numTasks,
                messages=[],
                timestamp=time.time())

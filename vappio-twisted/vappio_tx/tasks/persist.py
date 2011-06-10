import time

import pymongo

from twisted.internet import threads
from twisted.internet import defer

from twisted.python import reflect

from igs.utils import functional as func

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

class Error(Exception):
    pass

class TaskNotFoundError(Error):
    pass


class Task(func.Record):
    def __init__(self,
                 name,
                 tType,
                 state,
                 completedTasks,
                 numTasks,
                 messages,
                 timestamp):
        func.Record.__init__(self,
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


def _taskToDoc(t):
    return dict(name=t.name,
                tType=t.tType,
                state=t.state,
                completedTasks=t.completedTasks,
                numTasks=t.numTasks,
                messages=t.messages,
                timestamp=t.timestamp)

def _taskFromDoc(d):
    return Task(name=d['name'],
                tType=d['tType'],
                state=d['state'],
                completedTasks=d['completedTasks'],
                numTasks=d['numTasks'],
                messages=d['messages'],
                timestamp=d['timestamp'])


taskFromDict = _taskFromDoc
taskToDict = _taskToDoc

def createTask(name, tType, state, numTasks):
    return Task(name=name,
                tType=tType,
                state=state,
                completedTasks=0,
                numTasks=numTasks,
                messages=[],
                timestamp=time.time())


def loadTasksBy(criteria):
    return threads.deferToThread(lambda : [_taskFromDoc(t)
                                           for t in pymongo.Connection().clovr.tasks.find(criteria)])

def loadAllTasks():
    return loadTasksBy({})

@defer.inlineCallbacks
def loadTask(taskName):
    tasks = yield loadTasksBy({'name': taskName})

    if not tasks:
        raise TaskNotFoundError(taskName)

    defer.returnValue(tasks[0])


def saveTask(task):
    doc = func.updateDict({'_id': task.name},
                          _taskToDoc(task))
                           
    return threads.deferToThread(lambda : pymongo.Connection().clovr.tasks.save(doc, safe=True)).addCallback(lambda _ : task)

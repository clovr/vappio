#
# This manages tags.  The following actions are supported:
#
# tagData - Tag a dataset, overwrite or append, including metadata - async
# deleteTag - Delete a tag, this could include deleting dataset as well - async
# describeTags - Give detailed information on a provided set of tags - sync
# describeTagsLite - Give lite information on all tags in the system *debating the existence of this* - sync
# serviceStatus - Information about the service, such as tags currently being executed - sync

from twisted.internet import defer
from twisted.internet import reactor

from twisted.python import log

from vappio.tasks import task

from vappio_tx.utils import queue
from vappio_tx.utils import core as vappio_tx_core

from vappio_tx.mq import client

from vappio_tx.tasks import tasks as tasks_tx



class State:
    def __init__(self, conf):
        self.conf = conf
        self.runningTagging = {}
        self.runningDelete = {}
        self.tagsCache = {}


def subscribeIdempotent(mq, idempotentF, taskT, url, frontQueue, workQueue, concurrent):
    """
    mq - Message queue to subscribe.
    idempotentF - Function to determine if the request has already happened.  Returns (True, retval)
                  if it has, and (False, _) if it hasn't.
    taskT - The type of the task to create.
    url - If the request is destined for another cluster, this is the URL that should be requested.
    fronQueue - The queue that requests will come in on.
    workQueue - The queue to forward requests that have not already taken place to.
    concurrent - The number of requests to run concurrently
    
    Performs the following steps:
    1) If a request is destined for another cluster, forward it to said cluster and return the result
    2) Run idempotentF on the request to determine if the request has been done before, if so return value
    3) If not, create a task and forward work to workQueue
    """
    # decode json -> forward (run (idempotent)) -> task id -> return to user
    def createTaskAndForward(mq, destQueue, tType, numTasks, body):
        d = tasks.createTaskAndSave(tType, numTasks)
        
        def _forward(taskName):
            body['task_name'] = taskName
            mq.send(destQueue, json.dumps(body))
            return taskName

        d.addCallback(_forward)
        return d
    
    def _idempotent(mq, body):
        def _performWorkIfNeeded(r):
            exists, retVal = r
            # If it exists than return the value already there,
            # if not, create the task and forward on
            if exists:
                return retVal
            else:
                return createTaskAndForward(mq,
                                            workQueue,
                                            taskT,
                                            1,
                                            body)

        idempotentDefer = idempotentF(mq, body)
        idempotentDefer.addCallback(_performWorkIfNeeded)
        return idempotentDefer

    
    queue.ensureRequestAndSubscribeForward(mq,
                                           _idempotentF,
                                           url,
                                           frontQueue,
                                           concurrent)

    queue.subscribe(mq, qs, workQueue, concurrent)

    
def subscribeToQueues(state, mq):
    # Just a shorthand definition
    queueSubscription = vappio_tx_core.QueueSubscription

    successF = lambda f : lambda mq, body : f(state, mq, body)
    failTaskF = lambda mq, body, f : 'task_name' in body and tasks_tx.updateTask(body['task_name'],
                                                                                 lambda t : t.setState(task.TASK_FAILED
                                                                                                       ).addFailure(f))

    returnQueueFailF = lambda mq, body, f : queue.returnQueueFailure(mq, body['return_queue'], f)

    
    
def makeService(conf):
    mqService = client.makeService(conf)
    mqFactory = mqService.mqFactory

    state = State(conf)

    startUpDefer = loadAllTags(state)
    startUpDefer.addCallback(lambda _ : subscribeToQueues(state, mqFactory))

    return mqService



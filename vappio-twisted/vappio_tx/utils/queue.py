import sys
import time
import json

from twisted.python import reflect

from igs.utils import functional as func

from igs_tx.utils import errors
from igs_tx.utils import global_state
from igs_tx.utils import http

from vappio_tx.utils import core as vappio_tx_core

from vappio_tx.tasks import tasks

from vappio_tx.internal_client import clusters as clusters_client

class RemoteError(Exception):
    def __init__(self, name, msg, stacktrace):
        self.name = name
        self.msg = msg
        self.stacktrace = stacktrace

    def __str__(self):
        return 'RemoteError(%r)' % ((self.name, self.msg, self.stacktrace),)


def randomQueueName(baseName):
    return '/queue/' + baseName + '-' + global_state.make_ref()


def returnQueueSuccess(mq, queue, data):
    mq.send(queue, json.dumps({'success': True,
                               'data': data}))
    return data

def returnQueueFailure(mq, queue, failure):
    mq.send(queue, json.dumps({'success': False,
                               'data': {'stacktrace': errors.stackTraceToString(failure),
                                        'name': '',
                                        'msg': failure.getErrorMessage()}}))
    return failure

def returnQueueError(mq, queue, msg):
    mq.send(queue, json.dumps({'success': False,
                               'data': {'stacktrace': '',
                                        'name': '',
                                        'msg': msg}}))
    return None

def returnQueueException(mq, queue):
    excType, excValue, _traceback = sys.exc_info()
    mq.send(queue, json.dumps({'success': False,
                               'data': {'stacktrace': errors.getStacktrace(),
                                        'name': reflect.fullyQualifiedName(excType),
                                        'msg': str(excValue)}}))
    return None

def createTaskAndForward(mq, destQueue, tType, numTasks, body):
    d = tasks.createTaskAndSave(tType, numTasks)
    
    def _forward(taskName):
        body['task_name'] = taskName
        mq.send(destQueue, json.dumps(body))
        returnQueueSuccess(mq, body['return_queue'], taskName)

    def _error(f):
        returnQueueFailure(mq, body['return_queue'], f)
        return f
    
    d.addCallback(_forward)
    d.addErrback(_error)
    return d

def forwardRequestToCluster(mq, body, f, url):
    """
    Determine if the message should be forwarded, and if so forwards it.
    """
    if body['cluster'] == 'local':
        return f(mq, body)
    else:
        clusterDefer = clusters_client.loadCluster(body['cluster'], body['user_name'])

        def _askRemoteServer(cl):
            httpDefer = http.performQuery(cl['master']['public_dns'],
                                          url,
                                          func.updateDict(body, {'cluster': 'local'}))
            httpDefer.addCallback(lambda d : returnQueueSuccess(mq,
                                                                body['return_queue'],
                                                                d))
            httpDefer.addErrback(lambda f : returnQueueFailure(mq,
                                                               body['return_queue'],
                                                               f))
            return httpDefer
            
        clusterDefer.addCallback(_askRemoteServer)
        return clusterDefer
                                                  

def ensureRequestAndSubscribe(mqFactory, subscription, queue, concurrent):
    """
    Subscribes to a queue using the queue subscription that will only accept
    N concurrent requests
    """
    mqFactory.subscribe(subscription,
                        queue,
                        {'prefetch': concurrent})


def ensureRequestAndSubscribeTask(mqFactory, subscription, taskType, srcQueue, dstQueue, concurrent):
    """
    Subscribes to srcQueue and forwards to dstQueue, creating a
    task in the process.  The task name is given to the originaly requester
    and to the dstQueue.
    """
    forwardF = lambda mq, body : createTaskAndForward(mq,
                                                      dstQueue,
                                                      taskType,
                                                      1,
                                                      body)
    returnQueueF = lambda mq, body, failure : returnQueueFailure(mq, body['return_queue'], failure)

    #
    # Subscribe to the queue that will forward
    mqFactory.subscribe(subscription.setSuccess(forwardF).setFailure(returnQueueF),
                        srcQueue)

    #
    # Subscribe to the queue that will be forwarded to
    ensureRequestAndSubscribe(mqFactory,
                              subscription,
                              dstQueue,
                              concurrent)

def ensureRequestAndSubscribeForward(mqFactory, subscription, url, queue, concurrent):
    """
    Subscribes to a queue and will forward message to another cluster if they are not
    destined for this one
    """
    subscriptionNew = subscription.setSuccess(lambda mq, body : forwardRequestToCluster(mq,
                                                                                        body,
                                                                                        subscription.successF,
                                                                                        url=url))
    
    ensureRequestAndSubscribe(mqFactory,
                              subscriptionNew,
                              queue,
                              concurrent)
    
def ensureRequestAndSubscribeForwardTask(mqFactory, subscription, taskType, url, srcQueue, dstQueue, concurrent):
    """
    This is for the case where you want to forward a request to the appropriate cluster if necessarily
    but if there is no forwarding you want to create a task and push the request to another queue
    for final processing.
    """
    forwardF = lambda mq, body : createTaskAndForward(mq,
                                                      dstQueue,
                                                      taskType,
                                                      1,
                                                      body)
    ensureRequestAndSubscribeForward(mqFactory,
                                     subscription.setSuccess(forwardF),
                                     url,
                                     srcQueue,
                                     concurrent)

    ensureRequestAndSubscribe(mqFactory,
                              subscription,
                              dstQueue,
                              concurrent)

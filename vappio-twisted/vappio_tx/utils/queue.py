import sys
import json

from twisted.python import reflect


from igs.utils import functional as func
from igs.utils import core

from igs_tx.utils import errors
from igs_tx.utils import global_state
from igs_tx.utils import http
from igs_tx.utils import defer_pipe

from vappio_tx.tasks import tasks

from vappio_tx.internal_client import clusters as clusters_client

class RemoteError(Exception):
    def __init__(self, name, msg, stacktrace):
        self.name = name
        self.msg = msg
        self.stacktrace = stacktrace

    def __str__(self):
        return 'RemoteError(%r)' % ((self.name, self.msg, self.stacktrace),)

class QueueRequest(func.Record):
    def __init__(self, mq, msg):
        self.mq = mq
        self.msg = msg
        self.body = json.loads(msg.body)
    
def randomQueueName(baseName):
    return '/topic/' + baseName + '-' + global_state.make_ref()


def returnQueueSuccess(mq, queue, data):
    mq.send(queue, json.dumps({'success': True,
                               'data': data}))
    return data

def returnQueueFailure(mq, queue, failure):
    mq.send(queue, json.dumps({'success': False,
                               'data': {'stacktrace': errors.stackTraceToString(failure),
                                        'name': errors.failureExceptionName(failure),
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


def decodeRequest((mq, msg)):
    return defer_pipe.ret(QueueRequest(mq, msg))

def createTaskAndForward(dstQueue, tType, numTasks):
    """
    Return a function that, on each invocation will
    create a task with type tType and number of tasks numTasks
    and return a deferred which returns that (mq, body) where body has
    an attribute `task_name`
    """
    def _(request):
        def _forward(taskName):
            request.body['task_name'] = taskName
            request.mq.send(dstQueue, json.dumps(request.body))
            return defer_pipe.ret(request.update(response=taskName))

        d = tasks.createTaskAndSave(tType, numTasks)
        d.addCallback(_forward)
        return d

    return _


def forwardRequestToCluster(url):
    """
    If the cluster described in `body` is not `local` then forward the request
    to the provided URL, otherwise return whatever f returns.  f must return
    a deferred
    """
    def _(request):
        if request.body['cluster'] == 'local':
            return defer_pipe.ret(request)
        else:
            clusterDefer = clusters_client.loadCluster(request.body['cluster'],
                                                       request.body['user_name'])

            def _askRemoteServer(cl):
                return http.performQuery(cl['master']['public_dns'],
                                         url,
                                         func.updateDict(request.body, {'cluster': 'local'}),
                                         timeout=10,
                                         tries=1)

            def _setResponse(r):
                return request.update(response=r)
            
            clusterDefer.addCallback(_askRemoteServer)
            clusterDefer.addCallback(_setResponse)
            return defer_pipe.emitDeferred(clusterDefer)

    return _


def subscribe(mq, queue, concurrent, subscription):
    """
    Subscribes to a queue using the queue subscription that will only accept
    N concurrent requests
    """
    mq.subscribe(lambda mq, msg : defer_pipe.runPipe(subscription, (mq, msg)),
                 queue,
                 {'prefetch': concurrent})

    
def exceptionMsg(exn, request):
    """
    Takes a message queue, a dictionary that must contain the key `return_queue`
    and an exception, the exception will be dumped to json
    """
    returnQueueError(request.mq, request.body['return_queue'], str(exn))
    return defer_pipe.ret(request)

def failureMsg(f, request):
    """
    Takes a message queue, a dictionary that must contain the key `return_queue`
    and a failure, the failure will be dumped to json
    """
    returnQueueFailure(request.mq, request.body['return_queue'], f)
    return defer_pipe.ret(request)

def ackMsg(request):
    request.mq.ack(request.msg.headers['message-id'])
    return defer_pipe.ret(request)

def ackMsgFailure(f, request):
    request.mq.ack(request.msg.headers['message-id'])
    return defer_pipe.ret(request)

def hookFailure(pipe):
    return defer_pipe.hookError(pipe,
                                failureMsg)

def returnSuccess(request):
    returnQueueSuccess(request.mq, request.body['return_queue'], request.response)
    return defer_pipe.ret(request)

def returnResponse(pipe):
    return hookFailure(defer_pipe.pipe([defer_pipe.runPipeCurry(pipe),
                                        returnSuccess]))

def keysInBody(ks):
    def _(request):
        if core.keysInDict(ks, request.body):
            return defer_pipe.ret(request)
        else:
            raise Exception('Missing keys in request %r %r' % (ks, request.body))

    return _


def wrapRequestHandler(state, f):
    _addState = lambda r : defer_pipe.ret(r.update(state=state))
    
    return defer_pipe.pipe([decodeRequest,
                            defer_pipe.hookError(defer_pipe.pipe([keysInBody(['return_queue']),
                                                                  _addState,
                                                                  f,
                                                                  ackMsg]),
                                                 ackMsgFailure)])

def wrapRequestHandlerTask(state, f):
    _f = defer_pipe.hookError(defer_pipe.pipe([f, tasks.setRequestComplete]),
                              tasks.setRequestFailed)
    return wrapRequestHandler(state, _f)
                            

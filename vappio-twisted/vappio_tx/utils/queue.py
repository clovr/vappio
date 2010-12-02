import sys
import time
import json

from twisted.python import reflect

from igs_tx.utils import errors

RANDOM_QUEUE_STATE = 0

class RemoteError(Exception):
    def __init__(self, name, msg, stacktrace):
        self.name = name
        self.msg = msg
        self.stacktrace = stacktrace

    def __str__(self):
        return 'RemoteError(%r)' % ((self.name, self.msg, self.stacktrace),)


def randomQueueName(baseName):
    # Evil I know, storing state like this
    global RANDOM_QUEUE_STATE
    # The 10000 is arbitrary here
    if RANDOM_QUEUE_STATE > 10000:
        RANDOM_QUEUE_STATE = 0
    else:
        RANDOM_QUEUE_STATE += 1
    return '/queue/' + baseName + '-' + str(time.time()) + '-' + str(RANDOM_QUEUE_STATE)


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

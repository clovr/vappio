from twisted.internet import defer

from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.credentials import credentials_misc

@defer_utils.timeIt
@defer.inlineCallbacks
def handleTerminateInstances(request):
    if request.body['instances']:
        yield request.credential.terminateInstances([request.credential.instanceFromDict(i)
                                                    for i in request.body['instances']])

        request.state.credentialsCache.invalidate(request.credential.name)

        queue.returnQueueSuccess(request.mq,
                                 request.body['return_queue'],
                                 True)
    else:
        queue.returnQueueSuccess(request.mq,
                                 request.body['return_queue'],
                                 True)
        
    defer.returnValue(request)

def subscribe(mq, state):
    processTerminateInstances = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name',
                                                                                        'instances']),
                                                                      credentials_misc.loadCredentialForRequest,
                                                                      handleTerminateInstances]),
                                                     queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.terminateinstances_queue'),
                    state.conf('credentials.concurrent_terminateinstances'),
                    queue.wrapRequestHandler(state, processTerminateInstances))

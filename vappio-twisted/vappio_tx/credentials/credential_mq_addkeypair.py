from twisted.internet import defer

from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.credentials import credentials_misc

@defer_utils.timeIt
@defer.inlineCallbacks
def handleAddKeypair(request):
    yield request.credential.addKeypair(request.body['keypair_name'])
    queue.returnQueueSuccess(request.mq,
                             request.body['return_queue'],
                             True)

    defer.returnValue(request)                             

def subscribe(mq, state):
    processAddKeypair = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name',
                                                                                'keypair_name']),
                                                              credentials_misc.loadCredentialForRequest,
                                                              handleAddKeypair]),
                                             queue.failureMsg)

    queue.subscribe(mq,
                    state.conf('credentials.addkeypair_queue'),
                    state.conf('credentials.concurrent_addkeypair'),
                    queue.wrapRequestHandler(state, processAddKeypair))

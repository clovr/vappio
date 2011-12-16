from twisted.internet import defer

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.credentials import credentials_misc

@defer.inlineCallbacks
def handleListKeypairs(request):
    keypairs = yield request.credential.listKeypairs()
    queue.returnQueueSuccess(request.mq,
                             request.body['return_queue'],
                             keypairs)

    defer.returnValue(request)

def subscribe(mq, state):
    processListKeypairs = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name']),
                                                                credentials_misc.loadCredentialForRequest,
                                                                handleListKeypairs]),
                                               queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.listkeypairs_queue'),
                    state.conf('credentials.concurrent_listkeypairs'),
                    queue.wrapRequestHandler(state, processListKeypairs))
    

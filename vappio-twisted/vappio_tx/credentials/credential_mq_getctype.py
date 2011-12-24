from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.credentials import credentials_misc

@defer_utils.timeIt
def handleGetCType(request):
    queue.returnQueueSuccess(request.mq,
                             request.body['return_queue'],
                             request.credential.credential.getCType())
    return defer_pipe.ret(request)

def subscribe(mq, state):
    processGetCType = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name']),
                                                            credentials_misc.loadCredentialForRequest,
                                                            handleGetCType]),
                                           queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.getctype_queue'),
                    state.conf('credentials.concurrent_getctype'),
                    queue.wrapRequestHandler(state, processGetCType))

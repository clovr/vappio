from igs.utils import functional as func
from igs.utils import config

from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.credentials import credentials_misc

@defer_utils.timeIt
def handleCredentialConfig(request):
    conf = config.configToDict(request.credential.credInstance.conf)
    conf = func.updateDict(conf,
                           {'general.ctype': request.credential.credential.getCType()})
    
    queue.returnQueueSuccess(request.mq, request.body['return_queue'], conf)
    
    return defer_pipe.ret(request)

def subscribe(mq, state):
    processCredentialConfig = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name']),
                                                                    credentials_misc.loadCredentialForRequest,
                                                                    handleCredentialConfig]),
                                                   queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.credentialconfig_queue'),
                    state.conf('credentials.concurrent_credentialconfig'),
                    queue.wrapRequestHandler(state, processCredentialConfig))

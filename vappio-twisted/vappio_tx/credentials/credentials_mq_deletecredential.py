from igs.utils import functional as func
from igs.utils import config

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.credentials import credentials_misc

def handleDeleteCredential(request):
    ## TODO: Handle the deletion of our credential here
    pass

def subscribe(mq, state):
    processDeleteCredential = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name']),
                                                                    credentials_misc.loadCredentialForRequest,
                                                                    handleDeleteCredential]),
                                                   queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.deletecredential_queue'),
                    state.conf('credentials.concurrent_deletecredential'),
                    queue.wrapRequestHandler(state, processCredentialConfig))

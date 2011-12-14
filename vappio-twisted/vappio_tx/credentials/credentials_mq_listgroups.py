from twisted.internet import defer

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.credentials import credentials_misc

@defer.inlineCallbacks
def handleListGroups(request):
    groups = yield request.credential.listGroups()
    queue.returnQueueSuccess(request.mq,
                             request.body['return_queue'],
                             groups)
    
    defer.returnValue(request)                             

def subscribe(mq, state):
    processListGroups = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name']),
                                                              credentials_misc.loadCredentialForRequest,
                                                              handleListGroups]),
                                             queue.failureMsg)

    queue.subscribe(mq,
                    state.conf('credentials.listgroups_queue'),
                    state.conf('credentials.concurrent_listgroups'),
                    queue.wrapRequestHandler(state, processListGroups))


from twisted.internet import defer

from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.credentials import credentials_misc

@defer_utils.timeIt
@defer.inlineCallbacks
def handleAddGroup(request):
    yield request.credential.addGroup(request.body['group_name'], request.body['group_description'])
    queue.returnQueueSuccess(request.mq,
                             request.body['return_queue'],
                             True)

    defer.returnValue(request)

def subscribe(mq, state):
    processAddGroup = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name',
                                                                              'group_name',
                                                                              'group_description']),
                                                            credentials_misc.loadCredentialForRequest,
                                                            handleAddGroup]),
                                           queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.addgroup_queue'),
                    state.conf('credentials.concurrent_addgroup'),
                    queue.wrapRequestHandler(state, processAddGroup))

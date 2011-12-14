from twisted.internet import defer

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.credentials import credentials_misc

@defer.inlineCallbacks
def handleAuthorizeGroup(request):
    yield request.credential.authorizeGroup(groupName=request.body['group_name'],
                                            protocol=request.body.get('protocol', None),
                                            portRange=request.body['port_range'],
                                            sourceGroup=request.body.get('source_group', None),
                                            sourceGroupUser=request.body.get('source_group_user', None),
                                            sourceSubnet=request.body.get('source_subnet', None))
    queue.returnQueueSuccess(request.mq,
                             request.body['return_queue'],
                             True)

    defer.returnValue(request)                             

def subscribe(mq, state):
    processAuthorizeGroup = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name',
                                                                                    'group_name',
                                                                                    'port_range']),
                                                                  credentials_misc.loadCredentialForRequest,
                                                                  handleAuthorizeGroup]),
                                                 queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.authorizegroup_queue'),
                    state.conf('credentials.concurrent_authorizegroup'),
                    queue.wrapRequestHandler(state, processAuthorizeGroup))

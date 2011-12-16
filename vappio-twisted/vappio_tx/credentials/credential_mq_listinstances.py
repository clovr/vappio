from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.credentials import credentials_misc

def handleListInstances(request):
    queue.returnQueueSuccess(request.mq,
                             request.body['return_queue'],
                             [request.credential.instanceToDict(i)
                              for i in request.state.credentialsCache.getCredential(request.credential.name)['instances']])

    return defer_pipe.ret(request)

def subscribe(mq, state):
    processListInstances = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name']),
                                                                 credentials_misc.loadCredentialForRequest,
                                                                 handleListInstances]),
                                                queue.failureMsg)

    queue.subscribe(mq,
                    state.conf('credentials.listinstances_queue'),
                    state.conf('credentials.concurrent_listinstances'),
                    queue.wrapRequestHandler(state, processListInstances))

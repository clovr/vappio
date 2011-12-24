from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.credentials import credentials_misc

@defer_utils.timeIt
def handleUpdateInstances(request):
    convertedInstances = [request.credential.instanceFromDict(i) for i in request.body['instances']]

    queue.returnQueueSuccess(request.mq,
                             request.body['return_queue'],
                             [request.credential.instanceToDict(ci) 
                              for ci in request.state.credentialsCache.getCredential(request.credential.name)['instances']
                              for i in convertedInstances 
                              if (ci.spotRequestId and ci.spotRequestId == i.spotRequestId) 
                              or ci.instanceId == i.instanceId])
    
    return defer_pipe.ret(request)

def subscribe(mq, state):
    processUpdateInstances = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name',
                                                                                     'instances']),
                                                                   credentials_misc.loadCredentialForRequest,
                                                                   handleUpdateInstances]),
                                                  queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.updateinstances_queue'),
                    state.conf('credentials.concurrent_updateinstances'),
                    queue.wrapRequestHandler(state, processUpdateInstances))

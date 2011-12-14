import os

from twisted.internet import defer

from igs_tx.utils import global_state
from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.credentials import credentials_misc

def handleRunSpotInstances(request):
    userDataFile=None
    if 'user_data' in request.body:
        userData = credentials_misc.replaceUserDataVariables(request.credential, request.body['user_data'])
        userDataFile = '/tmp/' + global_state.make_ref() + '.conf'
        fout = open(userDataFile, 'w')
        fout.write(userData + '\n')
        fout.close()    
        
    instances = yield request.credential.runSpotInstances(bidPrice=request.body['bid_price'],
                                                          amiId=request.body['ami'],
                                                          key=request.body['key'],
                                                          instanceType=request.body['instance_type'],
                                                          groups=request.body['groups'],
                                                          availabilityZone=request.body.get('availability_zone', None),
                                                          number=request.body.get('num_instances', 1),
                                                          userDataFile=userDataFile,
                                                          log=True)

    if userDataFile:
        os.remove(userDataFile)

    yield request.state.credentialsCache.invalidate(request.credential.name)
    
    queue.returnQueueSuccess(request.mq,
                             request.body['return_queue'],
                             [request.credential.instanceToDict(i)
                              for i in instances])

    defer.returnValue(request)                                  

def subscribe(mq, state):
    processRunSpotInstances = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name',
                                                                                      'bid_price',
                                                                                      'ami',
                                                                                      'key',
                                                                                      'instance_type',
                                                                                      'groups',
                                                                                      'num_instances']),
                                                                    credentials_misc.loadCredentialForRequest,
                                                                    handleRunSpotInstances]),
                                                   queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.runspotinstances_queue'),
                    state.conf('credentials.concurrent_runspotinstances'),
                    queue.wrapRequestHandler(state, processRunSpotInstances))

    

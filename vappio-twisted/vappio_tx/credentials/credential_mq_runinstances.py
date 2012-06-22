import os 

from twisted.python import log

from twisted.internet import defer

from igs_tx.utils import global_state
from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.credentials import credentials_misc

@defer_utils.timeIt
@defer.inlineCallbacks
def handleRunInstances(request):
    credential = request.credential
    
    userDataFile=None
    if 'user_data' in request.body:
        userData = credentials_misc.replaceUserDataVariables(credential, request.body['user_data'])
        userDataFile = '/tmp/' + global_state.make_ref() + '.conf'
        fout = open(userDataFile, 'w')
        fout.write(userData + '\n')
        fout.close()
    
    instances = yield credential.runInstances(amiId=request.body['ami'],
                                              key=request.body['key'],
                                              instanceType=request.body['instance_type'],
                                              groups=request.body['groups'],
                                              availabilityZone=request.body.get('availability_zone', None),
                                              number=request.body.get('num_instances', 1),
                                              userDataFile=userDataFile,
                                              log=True)
        
    if userDataFile:
        os.remove(userDataFile)

    for i in instances:
        log.msg('INSTANCE: instance_id: %s public_dns: %s' % (i.instanceId, i.publicDNS))
        
    yield request.state.credentialsCache.invalidate(credential.name)
    
    queue.returnQueueSuccess(request.mq,
                             request.body['return_queue'],
                             [credential.instanceToDict(i)
                              for i in instances])
    defer.returnValue(request)                                  

def subscribe(mq, state):
    processRunInstances = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name',
                                                                                  'ami',
                                                                                  'key',
                                                                                  'instance_type',
                                                                                  'groups',
                                                                                  'num_instances']),
                                                                credentials_misc.loadCredentialForRequest,
                                                                handleRunInstances]),
                                               queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.runinstances_queue'),
                    state.conf('credentials.concurrent_runinstances'),
                    queue.wrapRequestHandler(state, processRunInstances))

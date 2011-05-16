#
# The credential manager has queue interfaces for both web requests and
# direct requests from other components on the queue.
#
# Web requests:
# Add credential - requires: cred name, description, ctype, cert, key; optional: metadata
# List credentials - requires: optional: list of credentials
# Delete credentials - requires: cred name list (not implemented yet)
#
# Requests directly off the queue (all of these require a return queue id as well):
# credentialConfig - req: cred name
# runInstances - req: cred name, ami, key, instance type, groups list; opt: availzone, number, userdata, userdatafile
# runSpotInstances - same as runInstances but requires bid price
# listInstances - req: cred name
# terminateInstances - req: cred name, instances
# updateInstances - req: cred name, instances
# listKeypairs - req: cred name
# addKeypair - req: cred name, key pair name
# listGroups - req: cred name
# addGroup - req: cred name, group name, group description
# authorizeGroup : req cred name, group name, prootcol, portRange, sourceGroup, sourceGrouPuser, sourceSubnet
#
import os
import time

from twisted.internet import defer
from twisted.internet import reactor

from twisted.python import log

from igs.utils import functional as func
from igs.utils import config
from igs.utils import core

from igs_tx.utils import global_state
from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue
from vappio_tx.mq import client
from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.credentials import persist


REFRESH_INTERVAL = 30

class CacheEntry(func.Record):
    def __init__(self, val):
        func.Record.__init__(self, entryTime=time.time(), value=val)

class State:
    """
    This represents the state for the manager, a place to put all cached data
    and anything else of value
    """
    def __init__(self, conf):
        self.conf = conf
        self.credInstanceCache = {}
        self.instanceCache = {}
        self.refreshInstancesDelayed = None


class CredentialInstance(func.Record):
    """
    This contains an instances of a credential returned from instantiateCredential, and the
    original credential
    """

    def __init__(self, cred, credInstance):
        _f = lambda f : lambda *args, **kwargs : f(credInstance, *args, **kwargs)
        
        func.Record.__init__(self,
                             name=cred.name,
                             credential=cred,
                             ctype=cred.ctype,
                             credInstance=credInstance,
                             #
                             # Method forwards
                             instanceFromDict=cred.ctype.instanceFromDict,
                             instanceToDict=cred.ctype.instanceToDict,
                             runInstances=_f(cred.ctype.runInstances),
                             runSpotInstances=_f(cred.ctype.runSpotInstances),
                             listInstances=_f(cred.ctype.listInstances),
                             updateInstances=_f(cred.ctype.updateInstances),
                             listGroups=_f(cred.ctype.listGroups),
                             listKeypairs=_f(cred.ctype.listKeypairs),
                             addKeypair=_f(cred.ctype.addKeypair),
                             addGroup=_f(cred.ctype.addGroup),
                             authorizeGroup=_f(cred.ctype.authorizeGroup),
                             terminateInstances=_f(cred.ctype.terminateInstances))

    
        
def loadAndCacheCredential(state, credName):
    if credName in state.credInstanceCache:
        return defer.succeed(state.credInstanceCache[credName].value)
    else:
        d = persist.loadCredential(credName)

        def _instantiate(cred):
            instantiateDefer = cred.ctype.instantiateCredential(cred.conf, cred)
            instantiateDefer.addCallback(lambda cr : CredentialInstance(cred, cr))
            return instantiateDefer

        d.addCallback(_instantiate)
        
        def _cacheCredential(cred):
            listInstancesDefer = cred.listInstances()

            def _cacheInstances(instances):
                state.instanceCache[cred.name] = CacheEntry(instances)
                state.credInstanceCache[credName] = CacheEntry(cred)
                return cred

            listInstancesDefer.addCallback(_cacheInstances)
            listInstancesDefer.addCallback(lambda _ : cred)
            
            return listInstancesDefer

        d.addCallback(_cacheCredential)
        return d

def refreshInstances(state):
    credIter = iter(state.credInstanceCache.values())

    def _refresh():
        try:
            cred = credIter.next()
            cred = cred.value

            d = cred.listInstances()

            def _cacheInstances(instances):
                #
                # Possible race condition here, what if you start some
                # instances while a refresh is happening?  They will be
                # possibly be lost.  Ignoring at this point but
                # must fix soon
                state.instanceCache[cred.name] = CacheEntry(instances)
                return state.instanceCache[cred.name].value

            def _logAndConsumeError(f):
                log.err(f)
                return None

            d.addCallback(_cacheInstances)
            d.addErrback(_logAndConsumeError)

            d.addCallback(lambda _ : _refresh())
            return d
        except StopIteration:
            return None
        
    d = defer.succeed(None)
    d.addCallback(lambda _ : _refresh())

    def _refreshAgain(_ignore):
        state.refreshInstancesDelayed = reactor.callLater(REFRESH_INTERVAL, refreshInstances, state)

    d.addCallback(_refreshAgain)
    
def cacheInstances(instances, cred, state):
    cachedInstances = state.instanceCache.get(cred.name, CacheEntry([])).value
    cachedInstances.extend(instances)
    state.instanceCache[cred.name] = CacheEntry(cachedInstances)
    return instances


def replaceUserDataVariables(cred, userData):
    userData = userData.replace('<TMPL_VAR NAME=CERT_FILE>', open(cred.credInstance.cert).read())
    userData = userData.replace('<TMPL_VAR NAME=PK_FILE>', open(cred.credInstance.pkey).read())
    userData = userData.replace('<TMPL_VAR NAME=CTYPE>', cred.credential.getCType())
    userData = userData.replace('<TMPL_VAR NAME=METADATA>', ','.join([str(k) + '=' + str(v) for k, v in cred.credential.metadata.iteritems()]))

    return userData


def handleGetCType(request):
    queue.returnQueueSuccess(request.mq,
                             request.body['return_queue'],
                             request.credential.credential.getCType())
    return defer_pipe.ret(request)

def handleCredentialConfig(request):
    conf = config.configToDict(request.credential.credInstance.conf)
    conf = func.updateDict(conf,
                           {'general.ctype': request.credential.credential.getCType()})
    
    queue.returnQueueSuccess(request.mq, request.body['return_queue'], conf)
    
    return defer_pipe.ret(request)

def handleRunInstances(request):
    userDataFile=None
    if 'user_data' in request.body:
        userData = replaceUserDataVariables(request.credential, request.body['user_data'])
        userDataFile = '/tmp/' + global_state.make_ref() + '.conf'
        fout = open(userDataFile, 'w')
        fout.write(userData + '\n')
        fout.close()
    
    d = request.credential.runInstances(amiId=request.body['ami'],
                                        key=request.body['key'],
                                        instanceType=request.body['instance_type'],
                                        groups=request.body['groups'],
                                        availabilityZone=request.body.get('availability_zone', None),
                                        number=request.body.get('num_instances', 1),
                                        userDataFile=userDataFile,
                                        log=True)

    def _removeUserDataFile(instances):
        if userDataFile:
            os.remove(userDataFile)

        return instances

    d.addCallback(_removeUserDataFile)
    d.addCallback(cacheInstances, request.credential, request.state)
    
    d.addCallback(lambda instances : queue.returnQueueSuccess(request.mq,
                                                              request.body['return_queue'],
                                                              [request.credential.instanceToDict(i)
                                                               for i in instances]))
    d.addCallback(lambda _ : request)
    return d

def handleRunSpotInstances(request):
    userDataFile=None
    if 'user_data' in request.body:
        userData = replaceUserDataVariables(request.credential, request.body['user_data'])
        userDataFile = '/tmp/' + global_state.make_ref() + '.conf'
        fout = open(userDataFile, 'w')
        fout.write(userData + '\n')
        fout.close()    
        
    d = request.credential.runSpotInstances(bidPrice=request.body['bid_price'],
                                            amiId=request.body['ami'],
                                            key=request.body['key'],
                                            instanceType=request.body['instance_type'],
                                            groups=request.body['groups'],
                                            availabilityZone=request.body.get('availability_zone', None),
                                            number=request.body.get('num_instances', 1),
                                            userDataFile=userDataFile,
                                            log=True)

    def _removeUserDataFile(instances):
        if userDataFile:
            os.remove(userDataFile)

        return instances

    d.addCallback(_removeUserDataFile)
    d.addCallback(cacheInstances, request.credential, request.state)
    
    d.addCallback(lambda instances : queue.returnQueueSuccess(request.mq,
                                                              request.body['return_queue'],
                                                              [request.credential.instanceToDict(i)
                                                               for i in instances]))
    d.addCallback(lambda _ : request)
    return d
        
def handleListInstances(request):
    queue.returnQueueSuccess(request.mq,
                             request.body['return_queue'],
                             [request.credential.instanceToDict(i)
                              for i in request.state.instanceCache.get(request.credential.name, CacheEntry([])).value])

    return defer_pipe.ret(request)
    
def handleTerminateInstances(request):
    if request.body['instances']:
        d = request.credential.terminateInstances([request.credential.instanceFromDict(i)
                                                   for i in request.body['instances']])
        d.addCallback(lambda _ : queue.returnQueueSuccess(request.mq,
                                                          request.body['return_queue'],
                                                          True))
        d.addCallback(lambda _ : request)
        return d
    else:
        queue.returnQueueSuccess(request.mq,
                                 request.body['return_queue'],
                                 True)
        return defer_pipe.ret(request)

def handleUpdateInstances(request):
    convertedInstances = [request.credential.instanceFromDict(i) for i in request.body['instances']]
    queue.returnQueueSuccess(request.mq,
                             request.body['return_queue'],
                             [request.credential.instanceToDict(ci)
                              for ci in request.state.instanceCache.get(request.credential.name, CacheEntry([])).value
                              for i in convertedInstances
                              if (ci.spotRequestId and ci.spotRequestId == i.spotRequestId) or ci.instanceId == i.instanceId])
    
    return defer_pipe.ret(request)

def handleListKeypairs(request):
    d = request.credential.listKeypairs()
    d.addCallback(lambda keypairs : queue.returnQueueSuccess(request.mq,
                                                             request.body['return_queue'],
                                                             keypairs))
    d.addCallback(lambda _ : request)
    return d
    
def handleAddKeypair(request):
    d = request.credential.addKeypair(request.body['keypair_name'])
    d.addCallback(lambda _ : queue.returnQueueSuccess(request.mq,
                                                      request.body['return_queue'],
                                                      True))
    d.addCallback(lambda _ : request)
    return d

def handleListGroups(request):
    d = request.credential.listGroups()
    d.addCallback(lambda groups : queue.returnQueueSuccess(request.mq,
                                                           request.body['return_queue'],
                                                           groups))
    d.addCallback(lambda _ : request)
    return d

def handleAddGroup(request):
    d = request.credential.addGroup(request.body['group_name'], request.body['group_description'])
    d.addCallback(lambda _ : queue.returnQueueSuccess(request.mq,
                                                      request.body['return_queue'],
                                                      True))
    d.addCallback(lambda _ : request)
    return d

def handleAuthorizeGroup(request):
    d = request.credential.authorizeGroup(groupName=request.body['group_name'],
                                          protocol=request.body.get('protocol', None),
                                          portRange=request.body['port_range'],
                                          sourceGroup=request.body.get('source_group', None),
                                          sourceGroupUser=request.body.get('source_group_user', None),
                                          sourceSubnet=request.body.get('source_subnet', None))
    d.addCallback(lambda _ : queue.returnQueueSuccess(request.mq,
                                                      request.body['return_queue'],
                                                      True))
    d.addCallback(lambda _ : request)
    return d

def handleWWWListAddCredentials(request):
    if 'credential_name' in request.body and core.keysInDict(['credential_name',
                                                              'description',
                                                              'ctype',
                                                              'metadata'],
                                                            request.body):
        # Users can provide a file name or the actual contents of the
        # certificate.
        if 'cert_file' in request.body:
            cert = open(request.body['cert_file']).read()
        else:
            cert = request.body['cert']

        if 'pkey_file' in request.body:
            pkey = open(request.body['pkey_file']).read()
        else:
            pkey = request.body['pkey']
            
        cred = persist.createCredential(name=request.body['credential_name'],
                                        desc=request.body['description'],
                                        ctype=request.body['ctype'],
                                        cert=cert,
                                        pkey=pkey,
                                        active=True,
                                        metadata=request.body['metadata'],
                                        conf=config.configFromMap(request.body.get('conf', {}),
                                                                  base=config.configFromEnv()))
        d = persist.saveCredential(cred)
        d.addCallback(lambda _ : loadAndCacheCredential(request.state, request.body['credential_name']))
        d.addCallback(lambda _ : queue.returnQueueSuccess(request.mq,
                                                          request.body['return_queue'],
                                                          True))
        d.addCallback(lambda _ : request)
        return d
    elif 'credential_name' not in request.body:
        d = persist.loadAllCredentials()
        d.addCallback(lambda cs : queue.returnQueueSuccess(request.mq,
                                                           request.body['return_queue'],
                                                           [{'name': c.name,
                                                             'description': c.desc,
                                                             'num_instances': len(request.state.instanceCache.get(c.name, CacheEntry([])).value),
                                                             'ctype': c.getCType()}
                                                            for c in cs
                                                            if ('credential_names' in request.body and c.name in request.body['credential_names']) or
                                                            'credential_names' not in request.body]))
        d.addCallback(lambda _ : request)
        return d
    else:
        queue.returnQueueError(request.mq,
                               request.body['return_queue'],
                               'Unknown credential query')        
        d = defer.fail(Exception('Unknown request: ' + str(request.body)))
        return d




def loadCredentials(state):
    d = persist.loadAllCredentials()
    d.addCallback(lambda cs : defer.DeferredList([loadAndCacheCredential(state, c.name)
                                                  for c in cs]))
        
    def _refreshInstances(_ignore):
        state.refreshInstancesDelayed = reactor.callLater(0, refreshInstances, state)

    def _logErrorAndTryAgainSoon(f):
        log.err(f)
        reactor.callLater(10, loadCredentials, state)

    d.addCallback(_refreshInstances)
    d.addErrback(_logErrorAndTryAgainSoon)
    return d


def loadCredentialForRequest(request):
    d = loadAndCacheCredential(request.state, request.body['credential_name'])
    d.addCallback(lambda c : request.update(credential=c))
    return d

def subscribeToQueues(mq, state):
    # Queue frontend
    processGetCType = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name']),
                                                            loadCredentialForRequest,
                                                            handleGetCType]),
                                           queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.getctype_queue'),
                    state.conf('credentials.concurrent_getctype'),
                    queue.wrapRequestHandler(state, processGetCType))
    
    processCredentialConfig = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name']),
                                                                    loadCredentialForRequest,
                                                                    handleCredentialConfig]),
                                                   queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.credentialconfig_queue'),
                    state.conf('credentials.concurrent_credentialconfig'),
                    queue.wrapRequestHandler(state, processCredentialConfig))


    processRunInstances = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name',
                                                                                  'ami',
                                                                                  'key',
                                                                                  'instance_type',
                                                                                  'groups',
                                                                                  'num_instances']),
                                                                loadCredentialForRequest,
                                                                handleRunInstances]),
                                               queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.runinstances_queue'),
                    state.conf('credentials.concurrent_runinstances'),
                    queue.wrapRequestHandler(state, processRunInstances))
    

    processRunSpotInstances = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name',
                                                                                      'bid_price',
                                                                                      'ami',
                                                                                      'key',
                                                                                      'instance_type',
                                                                                      'groups',
                                                                                      'num_instances']),
                                                                    loadCredentialForRequest,
                                                                    handleRunSpotInstances]),
                                                   queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.runspotinstances_queue'),
                    state.conf('credentials.concurrent_runspotinstances'),
                    queue.wrapRequestHandler(state, processRunSpotInstances))


    processListInstances = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name']),
                                                                 loadCredentialForRequest,
                                                                 handleListInstances]),
                                                queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.listinstances_queue'),
                    state.conf('credentials.concurrent_listinstances'),
                    queue.wrapRequestHandler(state, processListInstances))


    processTerminateInstances = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name',
                                                                                        'instances']),
                                                                      loadCredentialForRequest,
                                                                      handleTerminateInstances]),
                                                     queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.terminateinstances_queue'),
                    state.conf('credentials.concurrent_terminateinstances'),
                    queue.wrapRequestHandler(state, processTerminateInstances))
    

    processUpdateInstances = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name',
                                                                                     'instances']),
                                                                   loadCredentialForRequest,
                                                                   handleUpdateInstances]),
                                                  queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.updateinstances_queue'),
                    state.conf('credentials.concurrent_updateinstances'),
                    queue.wrapRequestHandler(state, processUpdateInstances))

    processListKeypairs = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name']),
                                                                loadCredentialForRequest,
                                                                handleListKeypairs]),
                                               queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.listkeypairs_queue'),
                    state.conf('credentials.concurrent_listkeypairs'),
                    queue.wrapRequestHandler(state, processListKeypairs))
    

    processAddKeypair = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name',
                                                                                'keypair_name']),
                                                              loadCredentialForRequest,
                                                              handleAddKeypair]),
                                             queue.failureMsg)

    queue.subscribe(mq,
                    state.conf('credentials.addkeypair_queue'),
                    state.conf('credentials.concurrent_addkeypair'),
                    queue.wrapRequestHandler(state, processAddKeypair))
    

    processListGroups = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name']),
                                                              loadCredentialForRequest,
                                                              handleListGroups]),
                                             queue.failureMsg)

    queue.subscribe(mq,
                    state.conf('credentials.listgroups_queue'),
                    state.conf('credentials.concurrent_listgroups'),
                    queue.wrapRequestHandler(state, processListGroups))


    processAddGroup = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name',
                                                                              'group_name',
                                                                              'group_description']),
                                                            loadCredentialForRequest,
                                                            handleAddGroup]),
                                           queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.addgroup_queue'),
                    state.conf('credentials.concurrent_addgroup'),
                    queue.wrapRequestHandler(state, processAddGroup))
    

    processAuthorizeGroup = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name',
                                                                                    'group_name',
                                                                                    'port_range']),
                                                                  loadCredentialForRequest,
                                                                  handleAuthorizeGroup]),
                                                 queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.authorizegroup_queue'),
                    state.conf('credentials.concurrent_authorizegroup'),
                    queue.wrapRequestHandler(state, processAuthorizeGroup))
    

    #
    # WWW Frontend
    processWWWListAddCredentials = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['cluster']),
                                                                         queue.forwardRequestToCluster(
                                                                             state.conf('www.url_prefix') + '/' +
                                                                             os.path.basename(state.conf('credentials.listaddcredentials_www'))),
                                                                         handleWWWListAddCredentials]),
                                                        queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.listaddcredentials_www'),
                    state.conf('credentials.concurrent_listaddcredentials'),
                    queue.wrapRequestHandler(state, processWWWListAddCredentials))

    
def makeService(conf):
    mqService = client.makeService(conf)

    state = State(conf)

    d = loadCredentials(state)
    d.addCallback(lambda _ : subscribeToQueues(mqService.mqFactory, state))

    return mqService
    

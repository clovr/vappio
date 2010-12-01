#
# The credential manager has queue interfaces for both web requests and
# direct requests from other components on the queue.
#
# Web requests:
# Add credential - requires: username, cred name, description, ctype, cert, key; optional: metadata
# List credentials - requires: username
# Delete credentials - requires: username, cred name list
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
import time
import json

from twisted.internet import defer
from twisted.internet import reactor

from twisted.python import log

from igs.utils import functional as func
from igs.utils import config

from vappio_tx.utils import queue
from vappio_tx.mq import client

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
    def __init__(self):
        self.credInstanceCache = {}
        self.instanceCache = {}
        self.refreshInstancesDelayed = None

def loadAndCacheCredential(state, credName):
    if credName in state.credInstanceCache:
        return defer.succeed(state.credInstanceCache[credName].value)
    else:
        d = persist.loadCredential(credName)

        d.addCallback(lambda c : c.ctype.instantiateCredential(config.configFromEnv(), c))
        
        def _cacheCredential(cred):
            state.credInstanceCache[credName] = CacheEntry(cred)
            return cred

        d.addCallback(_cacheCredential)
        return d

def refreshInstances(state):
    credIter = iter(state.credInstanceCache.values())

    def _refresh():
        try:
            cred = credIter.next()

            cachedInstances = state.instanceCache
            
            d = cred.ctype.listInstances(cred)

            def _cacheInstances(instances):
                if state.instanceCache.entryTime == cachedInstances.entryTime:
                    state.instanceCache[cred.name] = CacheEntry(instances)
                else:
                    instanceMap = {}
                    for i in state.instanceCache.value + instances:
                        if i.spotRequestId:
                            instanceMap[i.spotRequestId] = i
                        else:
                            instanceMap[i.instanceId] = i

                    state.instanceCache = CacheEntry(instanceMap.values())

                return state.instanceCache.value

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
    
def handleCredentialConfig(cred, state, mq, request):
    conf = {}
    for k in cred.conf.keys():
        conf[k] = cred.conf(k)
        
    queue.returnQueueSuccess(mq, request['return_queue'], conf)

def handleRunInstances(cred, state, mq, request):
    d = cred.ctype.runInstances(cred,
                                amiId=request['ami'],
                                key=request['key'],
                                instanceType=request['instance_type'],
                                groups=request['groups'],
                                availabilityZone=request.get('availability_zone', None),
                                number=request.get('num_instances', 1),
                                userData=request.get('user_data', None),
                                userDataFile=request.get('user_data_file'),
                                log=True)
    d.addCallback(cacheInstances)
    
    d.addCallback(lambda instances : queue.returnQueueSuccess(mq,
                                                              request['return_queue'],
                                                              [cred.ctype.instanceToDict(i)
                                                               for i in instances]))
    return d

def handleRunSpotInstances(cred, state, mq, request):
    d = cred.ctype.runInstances(cred,
                                bidPice=request['bid_price'],
                                amiId=request['ami'],
                                key=request['key'],
                                instanceType=request['instance_type'],
                                groups=request['groups'],
                                availabilityZone=request.get('availability_zone', None),
                                number=request.get('num_instances', 1),
                                userData=request.get('user_data', None),
                                userDataFile=request.get('user_data_file'),
                                log=True)
    d.addCallback(cacheInstances)
    
    d.addCallback(lambda instances : queue.returnQueueSuccess(mq,
                                                              request['return_queue'],
                                                              [cred.ctype.instanceToDict(i)
                                                               for i in instances]))
    return d
        
def handleListInstances(cred, state, mq, request):
    queue.returnQueueSuccess(mq,
                             request['return_queue'],
                             [cred.ctype.instanceToDict(i)
                              for i in state.instanceCache.get(cred.name, [])])
    
def handleTerminateInstances(cred, state, mq, request):
    d = cred.ctype.terminateInstances(cred,
                                      [cred.ctype.instanceFromDict(i)
                                       for i in request['instances']])
    d.addCallback(lambda _ : queue.returnQueueSuccess(mq,
                                                      request['return_queue'],
                                                      True))

def handleUpdateInstances(cred, state, mq, request):
    convertedInstances = [cred.ctype.instanceFromDict(i) for i in request['instances']]
    queue.returnQueueSuccess(mq,
                             request['return_queue'],
                             [ci
                              for ci in state.instanceCache.get(cred.name, [])
                              for i in convertedInstances
                              if (ci.spotRequestId and ci.spotRequestId == i.spotRequestId) or ci.instanceId == i.instanceId])
    
    

def handleListKeypairs(cred, state, mq, request):
    d = cred.ctype.listKeypairs(cred)
    d.addCallback(lambda keypairs : queue.returnQueueSuccess(mq,
                                                             request['return_queue'],
                                                             keypairs))
    return d
    
def handleAddKeypair(cred, state, mq, request):
    d = cred.ctype.addKeypair(cred, request['keypair_name'])
    d.addCallback(lambda _ : queue.returnQueueSuccess(mq,
                                                      request['return_queue'],
                                                      True))
    return d

def handleListGroups(cred, state, mq, request):
    d = cred.ctype.listGroups(cred)
    d.addCallback(lambda groups : queue.returnQueueSuccess(mq,
                                                           request['return_queue'],
                                                           groups))
    return d

def handleAddGroup(cred, state, mq, request):
    d = cred.ctype.addGroup(cred, request['group_name'], request['group_description'])
    d.addCallback(lambda _ : queue.returnQueueSuccess(mq,
                                                      request['return_queue'],
                                                      True))
    return d

def handleAuthorizeGroup(cred, state, mq, request):
    d = cred.ctype.authorizeGroup(cred,
                                  groupName=request['group_name'],
                                  protocol=request.get('protocol', None),
                                  portRange=request['port_range'],
                                  sourceGroup=request.get('source_group', None),
                                  sourceGroupUser=request.get('source_group_user', None),
                                  sourceSubnet=request.get('source_subnet', None))
    d.addCallback(lambda _ : queue.returnQueueSuccess(mq,
                                                      request['return_queue'],
                                                      True))
    return d

def handleWWWListAddCredential(state, mq, request):
    if 'cred_name' in request:
        cred = persist.createCredential(name=request['cred_name'],
                                        desc=request['description'],
                                        ctype=request['ctype'],
                                        cert=request['cert'],
                                        pkey=request['pkey'],
                                        active=True,
                                        metadata=request['metadata'])
        d = persist.saveCredential(cred)
        d.addCallback(lambda _ : loadAndCacheCredential(state, request['cred_name']))
        d.addCallback(lambda _ : queue.returnQueueSuccess(mq,
                                                          request['return_queue'],
                                                          True))
        return d
    else:
        d = persist.loadAllCredentials()
        d.addCallback(lambda cs : queue.returnQueueSuccess(mq,
                                                           request['return_queue'],
                                                           [{'name': c.name, 'description': c.desc}
                                                            for c in cs]))
        return d

def makeService(conf):
    mqService = client.makeService(conf)

    mqFactory = mqService.mqFactory

    state = State()

    def _loadCredentials():
        d = persist.loadAllCredentials()
        d.addCallback(lambda cs : defer.DeferredList([loadAndCacheCredential(state, c.name)
                                                      for c in cs]))
        
        def _refreshInstances(_ignore):
            state.refreshInstancesDelayed = reactor.callLater(0, refreshInstances, state)

        def _logErrorAndTryAgainSoon(f):
            log.err(f)
            reactor.callLater(10, _loadCredentials)

        d.addCallback(_refreshInstances)
        d.addErrback(_logErrorAndTryAgainSoon)
        return d

    reactor.callLater(0, _loadCredentials)
    
    def _mqFactoryF(f):
        def _validateMsg(m):
            try:
                v = json.loads(m.body)
                return 'return_queue' in v
            except:
                False
                
        def _handleMsg(m):
            if _validateMsg(m):
                body = json.loads(m.body)
                d = loadAndCacheCredential(state, body['credential_name'])
                d.addCallback(f, state, mqFactory, body)
                d.addErrback(lambda f : queue.returnQueueFailure(mqFactory, body['return_queue'], f))
            else:
                log.err('Incoming request failed verification: ' + m.body)
        return _handleMsg

    mqFactory.subscribe(_mqFactoryF(handleCredentialConfig),
                        conf('credentials.credentialconfig_queue'),
                        {'prefetch': int(conf('credentials.concurrent_credentialconfig'))})
    
    mqFactory.subscribe(_mqFactoryF(handleRunInstances),
                        conf('credentials.runinstances_queue'),
                        {'prefetch': int(conf('credentials.concurrent_runinstances'))})

    mqFactory.subscribe(_mqFactoryF(handleRunSpotInstances),
                        conf('credentials.runspotinstances_queue'),
                        {'prefetch': int(conf('credentials.concurrent_runspotinstances'))})
    
    mqFactory.subscribe(_mqFactoryF(handleListInstances),
                        conf('credentials.listinstances_queue'),
                        {'prefetch': int(conf('credentials.concurrent_listinstances'))})

    mqFactory.subscribe(_mqFactoryF(handleTerminateInstances),
                        conf('credentials.terminateinstances_queue'),
                        {'prefetch': int(conf('credentials.concurrent_terminateinstances'))})

    mqFactory.subscribe(_mqFactoryF(handleUpdateInstances),
                        conf('credentials.updateinstances_queue'),
                        {'prefetch': int(conf('credentials.concurrent_updateinstances'))})

    mqFactory.subscribe(_mqFactoryF(handleListKeypairs),
                        conf('credentials.listkeypairs_queue'),
                        {'prefetch': int(conf('credentials.concurrent_listkeypairs'))})

    mqFactory.subscribe(_mqFactoryF(handleAddKeypair),
                        conf('credentials.addkeypair_queue'),
                        {'prefetch': int(conf('credentials.concurrent_addkeypair'))})

    mqFactory.subscribe(_mqFactoryF(handleListGroups),
                        conf('credentials.listgroups_queue'),
                        {'prefetch': int(conf('credentials.concurrent_listgroups'))})

    mqFactory.subscribe(_mqFactoryF(handleAddGroup),
                        conf('credentials.addgroup_queue'),
                        {'prefetch': int(conf('credentials.concurrent_addgroup'))})

    mqFactory.subscribe(_mqFactoryF(handleAuthorizeGroup),
                        conf('credentials.authorizegroup_queue'),
                        {'prefetch': int(conf('credentials.concurrent_authorizegroup'))})


    #
    # Now add web frontend queues
    def _WWWRequest(f):
        def _validateMsg(m):
            try:
                v = json.loads(m.body)
                return 'return_queue' in v
            except:
                False
                
        def _handleMsg(m):
            if _validateMsg(m):
                d = defer.succeed(True)
                d.addCallback(lambda _ : f(state, mqFactory, json.loads(m.body)))
                d.addErrback(lambda f : queue.returnQueueFailure(mqFactory, json.loads(m.body)['return_queue'], f))
            else:
                log.err('Incoming www request failed verification: ' + m.body)

        return _handleMsg
    
    mqFactory.subscribe(_WWWRequest(handleWWWListAddCredential),
                        conf('credentials.listaddcredentials_queue'),
                        {'prefetch': int(conf('credentials.concurrent_listaddcredentials'))})
    
    return mqService
    

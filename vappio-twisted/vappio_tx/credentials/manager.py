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

from vappio_tx.utils import queue
from vappio_tx.utils import core as vappio_tx_core
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
            instantiateDefer = cred.ctype.instantiateCredential(config.configFromEnv(), cred)
            instantiateDefer.addCallback(lambda cr : CredentialInstance(cred, cr))
            return instantiateDefer

        d.addCallback(_instantiate)
        
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


def handleCredentialConfig(cred, state, mq, request):
    conf = {}
    for k in cred.credInstance.conf.keys():
        conf[k] = cred.credInstance.conf(k)
        
    queue.returnQueueSuccess(mq, request['return_queue'], conf)

def handleRunInstances(cred, state, mq, request):
    userDataFile=None
    if 'user_data' in request:
        userData = replaceUserDataVariables(cred, request['user_data'])
        userDataFile = '/tmp/' + global_state.make_ref() + '.conf'
        fout = open(userDataFile, 'w')
        fout.write(userData + '\n')
        fout.close()
    
    d = cred.runInstances(amiId=request['ami'],
                          key=request['key'],
                          instanceType=request['instance_type'],
                          groups=request['groups'],
                          availabilityZone=request.get('availability_zone', None),
                          number=request.get('num_instances', 1),
                          userDataFile=userDataFile,
                          log=True)

    def _removeUserDataFile(instances):
        if userDataFile:
            os.remove(userDataFile)

        return instances

    d.addCallback(_removeUserDataFile)    
    d.addCallback(cacheInstances, cred, state)
    
    d.addCallback(lambda instances : queue.returnQueueSuccess(mq,
                                                              request['return_queue'],
                                                              [cred.instanceToDict(i)
                                                               for i in instances]))
    return d

def handleRunSpotInstances(cred, state, mq, request):
    userDataFile=None
    if 'user_data' in request:
        userData = replaceUserDataVariables(cred, request['user_data'])
        userDataFile = '/tmp/' + global_state.make_ref() + '.conf'
        fout = open(userDataFile, 'w')
        fout.write(userData + '\n')
        fout.close()    
        
    d = cred.runInstances(bidPice=request['bid_price'],
                          amiId=request['ami'],
                          key=request['key'],
                          instanceType=request['instance_type'],
                          groups=request['groups'],
                          availabilityZone=request.get('availability_zone', None),
                          number=request.get('num_instances', 1),
                          userDataFile=userDataFile,
                          log=True)

    def _removeUserDataFile(instances):
        if userDataFile:
            os.remove(userDataFile)

        return instances

    d.addCallback(_removeUserDataFile)
    d.addCallback(cacheInstances, cred, state)
    
    d.addCallback(lambda instances : queue.returnQueueSuccess(mq,
                                                              request['return_queue'],
                                                              [cred.instanceToDict(i)
                                                               for i in instances]))
    return d
        
def handleListInstances(cred, state, mq, request):
    queue.returnQueueSuccess(mq,
                             request['return_queue'],
                             [cred.instanceToDict(i)
                              for i in state.instanceCache.get(cred.name, CacheEntry([])).value])

    
def handleTerminateInstances(cred, state, mq, request):
    d = cred.terminateInstances([cred.instanceFromDict(i)
                                 for i in request['instances']])
    d.addCallback(lambda _ : queue.returnQueueSuccess(mq,
                                                      request['return_queue'],
                                                      True))
    return d

def handleUpdateInstances(cred, state, mq, request):
    convertedInstances = [cred.instanceFromDict(i) for i in request['instances']]
    queue.returnQueueSuccess(mq,
                             request['return_queue'],
                             [cred.instanceToDict(ci)
                              for ci in state.instanceCache.get(cred.name, CacheEntry([])).value
                              for i in convertedInstances
                              if (ci.spotRequestId and ci.spotRequestId == i.spotRequestId) or ci.instanceId == i.instanceId])
    
    return defer.succeed(True)

def handleListKeypairs(cred, state, mq, request):
    d = cred.listKeypairs()
    d.addCallback(lambda keypairs : queue.returnQueueSuccess(mq,
                                                             request['return_queue'],
                                                             keypairs))
    return d
    
def handleAddKeypair(cred, state, mq, request):
    d = cred.addKeypair(request['keypair_name'])
    d.addCallback(lambda _ : queue.returnQueueSuccess(mq,
                                                      request['return_queue'],
                                                      True))
    return d

def handleListGroups(cred, state, mq, request):
    d = cred.listGroups()
    d.addCallback(lambda groups : queue.returnQueueSuccess(mq,
                                                           request['return_queue'],
                                                           groups))
    return d

def handleAddGroup(cred, state, mq, request):
    d = cred.addGroup(request['group_name'], request['group_description'])
    d.addCallback(lambda _ : queue.returnQueueSuccess(mq,
                                                      request['return_queue'],
                                                      True))
    return d

def handleAuthorizeGroup(cred, state, mq, request):
    d = cred.authorizeGroup(groupName=request['group_name'],
                            protocol=request.get('protocol', None),
                            portRange=request['port_range'],
                            sourceGroup=request.get('source_group', None),
                            sourceGroupUser=request.get('source_group_user', None),
                            sourceSubnet=request.get('source_subnet', None))
    d.addCallback(lambda _ : queue.returnQueueSuccess(mq,
                                                      request['return_queue'],
                                                      True))
    return d

def handleWWWListAddCredentials(state, mq, request):
    if 'credential_name' in request and core.keysInDict(['credential_name',
                                                         'description',
                                                         'ctype',
                                                         'cert',
                                                         'pkey',
                                                         'metadata'],
                                                        request):
        cred = persist.createCredential(name=request['credential_name'],
                                        desc=request['description'],
                                        ctype=request['ctype'],
                                        cert=request['cert'],
                                        pkey=request['pkey'],
                                        active=True,
                                        metadata=request['metadata'])
        d = persist.saveCredential(cred)
        d.addCallback(lambda _ : loadAndCacheCredential(state, request['credential_name']))
        d.addCallback(lambda _ : queue.returnQueueSuccess(mq,
                                                          request['return_queue'],
                                                          True))
        return d
    elif 'credential_name' not in request:
        d = persist.loadAllCredentials()
        d.addCallback(lambda cs : queue.returnQueueSuccess(mq,
                                                           request['return_queue'],
                                                           [{'name': c.name,
                                                             'description': c.desc,
                                                             'num_instances': len(state.instanceCache.get(c.name, CacheEntry([])).value)}
                                                            for c in cs
                                                            if ('credential_names' in request and c.name in request['credential_names']) or
                                                            'credential_names' not in request]))
        return d
    else:
        queue.returnQueueError(mq,
                               request['return_queue'],
                               'Unknown credential query')        
        d = defer.fail(Exception('Unknown request: ' + str(request)))
        return d

#
# Just a shorthand definition
queueSubscription = vappio_tx_core.QueueSubscription
    
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

    successF = lambda f : lambda mq, body : loadAndCacheCredential(state, body['credential_name']
                                                                   ).addCallback(f, state, mq, body)
    returnQueueF = lambda mq, body, f : queue.returnQueueFailure(mq, body['return_queue'], f)

    #
    # Queue frontend
    queue.ensureRequestAndSubscribe(mqFactory,
                                    queueSubscription(ensureF=core.keysInDictCurry(['credential_name']),
                                                      successF=successF(handleCredentialConfig),
                                                      failureF=returnQueueF),
                                    conf('credentials.credentialconfig_queue'),
                                    conf('credentials.concurrent_credentialconfig'))

    queue.ensureRequestAndSubscribe(mqFactory,
                                    queueSubscription(ensureF=core.keysInDictCurry(['credential_name',
                                                                                    'ami',
                                                                                    'key',
                                                                                    'instance_type',
                                                                                    'groups',
                                                                                    'num_instances']),
                                                      successF=successF(handleRunInstances),
                                                      failureF=returnQueueF),
                                    conf('credentials.runinstances_queue'),
                                    conf('credentials.concurrent_runinstances'))

    queue.ensureRequestAndSubscribe(mqFactory,
                                    queueSubscription(ensureF=core.keysInDictCurry(['credential_name',
                                                                                    'bid_price',
                                                                                    'ami',
                                                                                    'key',
                                                                                    'instance_type',
                                                                                    'groups',
                                                                                    'num_instances']),
                                                      successF=successF(handleRunSpotInstances),
                                                      failureF=returnQueueF),
                                    conf('credentials.runspotinstances_queue'),
                                    conf('credentials.concurrent_runspotinstances'))

    queue.ensureRequestAndSubscribe(mqFactory,
                                    queueSubscription(ensureF=core.keysInDictCurry(['credential_name']),
                                                      successF=successF(handleListInstances),
                                                      failureF=returnQueueF),
                                    conf('credentials.listinstances_queue'),
                                    conf('credentials.concurrent_listinstances'))
    
    queue.ensureRequestAndSubscribe(mqFactory,
                                    queueSubscription(ensureF=core.keysInDictCurry(['credential_name',
                                                                                    'instances']),
                                                      successF=successF(handleTerminateInstances),
                                                      failureF=returnQueueF),
                                    conf('credentials.terminateinstances_queue'),
                                    conf('credentials.concurrent_terminateinstances'))
    
    queue.ensureRequestAndSubscribe(mqFactory,
                                    queueSubscription(ensureF=core.keysInDictCurry(['credential_name',
                                                                                    'instances']),
                                                      successF=successF(handleUpdateInstances),
                                                      failureF=returnQueueF),
                                    conf('credentials.updateinstances_queue'),
                                    conf('credentials.concurrent_updateinstances'))

    queue.ensureRequestAndSubscribe(mqFactory,
                                    queueSubscription(ensureF=core.keysInDictCurry(['credential_name']),
                                                      successF=successF(handleListKeypairs),
                                                      failureF=returnQueueF),
                                    conf('credentials.listkeypairs_queue'),
                                    conf('credentials.concurrent_listkeypairs'))

    queue.ensureRequestAndSubscribe(mqFactory,
                                    queueSubscription(ensureF=core.keysInDictCurry(['credential_name',
                                                                                    'keypair_name']),
                                                      successF=successF(handleAddKeypair),
                                                      failureF=returnQueueF),
                                    conf('credentials.addkeypair_queue'),
                                    conf('credentials.concurrent_addkeypair'))
    

    queue.ensureRequestAndSubscribe(mqFactory,
                                    queueSubscription(ensureF=core.keysInDictCurry(['credential_name']),
                                                      successF=successF(handleListGroups),
                                                      failureF=returnQueueF),
                                    conf('credentials.listgroups_queue'),
                                    conf('credentials.concurrent_listgroups'))
    
    queue.ensureRequestAndSubscribe(mqFactory,
                                    queueSubscription(ensureF=core.keysInDictCurry(['credential_name',
                                                                               'group_name',
                                                                               'group_description']),
                                                      successF=successF(handleAddGroup),
                                                      failureF=returnQueueF),
                                    conf('credentials.addgroup_queue'),
                                    conf('credentials.concurrent_addgroup'))
    

    queue.ensureRequestAndSubscribe(mqFactory,
                                    queueSubscription(ensureF=core.keysInDictCurry(['credential_name',
                                                                                    'group_name',
                                                                                    'port_range']),
                                                      successF=successF(handleAuthorizeGroup),
                                                      failureF=returnQueueF),
                                    conf('credentials.authorizegroup_queue'),
                                    conf('credentials.concurrent_authorizegroup'))
    


    #
    # WWW Frontend
    queue.ensureRequestAndSubscribeForward(mqFactory,
                                           queueSubscription(ensureF=core.keysInDictCurry(['cluster']),
                                                             successF=lambda mq, body : handleWWWListAddCredentials(state, mq, body),
                                                             failureF=returnQueueF),
                                           conf('www.url_prefix') + '/' + os.path.basename(conf('credentials.listaddcredentials_www')),
                                           conf('credentials.listaddcredentials_www'),
                                           conf('credentials.concurrent_listaddcredentials'))

    
    return mqService
    

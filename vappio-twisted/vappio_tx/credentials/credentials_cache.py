from twisted.internet import defer
from twisted.internet import reactor

from twisted.python import log

from igs.utils import functional as func
from igs.utils import dependency

from igs_tx.utils import defer_work_queue
from igs_tx.utils import defer_utils

REFRESH_INTERVAL = 30

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

class CredentialsCache(dependency.Dependable):
    def __init__(self, state):
        dependency.Dependable.__init__(self)

        self.state = state
        self.workQueue = defer_work_queue.DeferWorkQueue(1)

    @defer.inlineCallbacks
    def initialize(self):
        self.cache = {}              
        self.state.credentialPersist.addDependent(self)
 
        yield self.workQueue.addWithDeferred(self.loadCredentials)
        yield self.workQueue.addWithDeferred(self.refreshInstances)
    
    def release(self):
        self.state.credentialPersist.removeDependent(self)
        return defer.succeed(None)
     
    def invalidate(self, credName):
        @defer.inlineCallbacks
        def _loadAndCache():
            credInstance = self.cache[credName]['cred_instance']
            instances = yield credInstance.listInstances()
            self.cache[credName]['instances'] = instances
            self.changed('save', credInstance)

        return self.workQueue.addWithDeferred(_loadAndCache)            
     
    def update(self, who, aspect, value):
        if who == self.state.credentialPersist:
            if aspect == 'load':
                # We don't want to do anything on load
                pass
            elif aspect == 'load_all':
                # Don't do anything on a load_all
                pass       
            elif aspect == 'save':
                self.workQueue.add(self.loadAndCacheCredential, value)
            elif aspect == 'delete':
                self.workQueue.add(self.deleteCredentialFromCache, value)
                pass
        
    @defer.inlineCallbacks
    def loadAndCacheCredential(self, credName):
        if credName in self.cache:
            defer.returnValue(self.cache[credName]['cred_instance'])
        else:
            cred = yield self.state.credentialPersist.loadCredential(credName)

            instantiatedCred = yield cred.ctype.instantiateCredential(cred.conf, cred)
            credInstance = CredentialInstance(cred, instantiatedCred)

            instances = yield credInstance.listInstances()
            self.cache[credName] = {'cred_instance': credInstance, 
                                    'instances': instances
                                   }

            defer.returnValue(credInstance)

    @defer.inlineCallbacks    
    def loadCredentials(self):
        credentials = yield self.state.credentialPersist.loadAllCredentials()

        try: 
            yield defer.DeferredList([self.loadAndCacheCredential(c.name)
                                      for c in credentials])

            self.state.refreshInstancesDelayed = reactor.callLater(0, self.refreshInstances)
        except Exception, err:        
            log.err(err)
            reactor.callLater(10, self.loadCredentials)

    def deleteCredentialFromCache(self, credential):
        try:
            self.cache.pop(credential)
        except Exception, e:
            log.err(e)            

        return defer.succeed(None)


    @defer.inlineCallbacks
    def refreshInstances(self):

        @defer.inlineCallbacks
        def _refresh(credDict):
            credInstance = credDict['cred_instance']

            try:
                instances = yield credInstance.listInstances()
                credDict['instances'] = instances
            except Exception, e:
                log.err(e)
                
        yield defer_utils.mapSerial(_refresh, self.cache.values())

        self.state.refreshInstancesDelayed = reactor.callLater(REFRESH_INTERVAL, self.refreshInstances)

    def getCredential(self, credName):
        return self.cache[credName]        

    def getAllCredentials(self):
        return self.cache


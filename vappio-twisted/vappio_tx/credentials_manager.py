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
from twisted.internet import reactor
from twisted.internet import defer

from vappio_tx.mq import client

from vappio_tx.credentials import persist
from vappio_tx.credentials import credentials_mq_listadd
from vappio_tx.credentials import credentials_mq_listinstances
from vappio_tx.credentials import credentials_mq_runinstances
from vappio_tx.credentials import credentials_mq_runspotinstances
from vappio_tx.credentials import credentials_mq_updateinstances
from vappio_tx.credentials import credentials_mq_terminateinstances
from vappio_tx.credentials import credentials_mq_listkeypairs
from vappio_tx.credentials import credentials_mq_addkeypair
from vappio_tx.credentials import credentials_mq_listgroups
from vappio_tx.credentials import credentials_mq_addgroup
from vappio_tx.credentials import credentials_mq_authorizegroup
from vappio_tx.credentials import credentials_mq_getctype
from vappio_tx.credentials import credentials_mq_credentialconfig
from vappio_tx.credentials import credentials_mq_deletecredential

from vappio_tx.credentials import credentials_cache

class State:
    """
    This represents the state for the manager, a place to put all cached data
    and anything else of value
    """
    def __init__(self, conf):
        self.conf = conf
        self.credentialPersist = persist.CredentialPersistManager()
        self.credentialsCache = credentials_cache.CredentialsCache(self)
        self.refreshInstancesDelayed = None

@defer.inlineCallbacks
def subscribeToQueues(mq, state):
    yield state.credentialsCache.initialize()
    
    yield defer.maybeDeferred(credentials_mq_listadd.subscribe, mq, state)
    yield defer.maybeDeferred(credentials_mq_listinstances.subscribe, mq, state)
    yield defer.maybeDeferred(credentials_mq_runinstances.subscribe, mq, state)
    yield defer.maybeDeferred(credentials_mq_runspotinstances.subscribe, mq, state)
    yield defer.maybeDeferred(credentials_mq_updateinstances.subscribe, mq, state)
    yield defer.maybeDeferred(credentials_mq_terminateinstances.subscribe, mq, state)
    yield defer.maybeDeferred(credentials_mq_listkeypairs.subscribe, mq, state)
    yield defer.maybeDeferred(credentials_mq_addkeypair.subscribe, mq, state)
    yield defer.maybeDeferred(credentials_mq_listgroups.subscribe, mq, state)
    yield defer.maybeDeferred(credentials_mq_addgroup.subscribe, mq, state)
    yield defer.maybeDeferred(credentials_mq_authorizegroup.subscribe, mq, state)
    yield defer.maybeDeferred(credentials_mq_getctype.subscribe, mq, state)
    yield defer.maybeDeferred(credentials_mq_credentialconfig.subscribe, mq, state)
    yield defer.maybeDeferred(credentials_mq_deletecredential.subscribe, mq, state)

def makeService(conf):
    mqService = client.makeService(conf)

    state = State(conf)
    reactor.callLater(0, subscribeToQueues, mqService.mqFactory, state)
    
    return mqService

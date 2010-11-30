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
import StringIO
import json

from twisted.python import log

from igs_tx.utils import commands
from igs_tx.utils import errors

from vappio_tx.mq import client

from igs.utils import functional as func


class State:
    """
    This represents the state for the manager, a place to put all cached data
    and anything else of value
    """
    def __init__(self):
        self.credInstanceMap = {}
        self.instanceCache = {}


def handleRunInstances(state, mq, request):
    pass

def handleRunSpotInstances(state, mq, request):
    pass

def handleListInstances(state, mq, request):
    pass

def handleTerminateInstances(state, mq, request):
    pass

def handleListInstances(state, mq, request):
    pass

def handleListKeypairs(state, mq, request):
    pass

def handleAddKeypair(state, mq, request):
    pass

def handleListGroups(state, mq, request):
    pass

def handleAddGroup(state, mq, request):
    pass

def handleAuthorizeGroup(state, mq, request):
    pass


def makeService(conf):
    mqService = client.makeService(conf)

    mqFactory = mqService.mqFactory

    state = State()
    
    def _mqFactoryF(f):
        def _verifyMsg(m):
            try:
                v = json.loads(m.body)
                return 'return_queue' in v
            except:
                False
                
        def _handleMsg(m):
            if _verifyMsg(m):
                f(state, mqFactory, json.loads(m.body))
            else:
                log.err('Incoming request failed verification: ' + m.body)
        return _handleMsg
    
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

    mqFactory.subscribe(_mqFactoryF(handleListInstances),
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
    
    return mqService
    

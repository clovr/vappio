##
# It's possible that somehow instances get lost in some sort of shuffle,
# although it shouldn't happen, where a controlling cluster doesn't
# terminate it and maybe somehow the child cannot terminate itself.
# This checks for such instances by finding instances that are not
# in our list of instances and if we can ssh into them adding
# them to a list to be killed after some time.
#
# NOTE: The code, as it exists, now, will NOT work properly if
# we get multiple user support.  Right now we sort of have
# mutliple user support but it's fake, everything is 'guest'
# so all of the operations call asthe guest user.
#
# THIS NEEDS SOME WORK BEFORE IT CAN BE MADE LIVE.  IF IT DOES
# NOT GO OUT IN A FEW MONTHS DELETE!
import time

from twisted.internet import reactor
from twisted.internet import defer

from twisted.python import log

from igs_tx.utils import defer_utils
from igs_tx.utils import ssh

from vappio_tx.internal_client import credentials as cred_client

from vappio_tx.internal_client import clusters as clusters_client

# Refresh cluster information every hour
REFRESH_FREQUENCY = 60 * 60

# When an instance times out
INSTANCE_TIMEOUT = 60 * 60 * 2

class State:
    def __init__(self, clustersState, mq):
        self.clustersState = clustersState
        self.mq = mq
        self.orphanedInstances = {}

def removeAdopted(credInstances, orphanedInstances):
    """Remove any instances that are no longer orphaned"""
    # Make sure we have a copy of the keys not just an iterator
    # since we'll be deleting
    for k in list(credInstances.keys()):
        if k not in orphanedInstances:
            credInstances.pop(k)

def updateOrphans(credInstances, orphanedInstances):
    """Udpate the time on all orphaned instances"""
    for orphaned in orphanedInstances:
        if orphaned not in credInstances:
            credInstances[orphaned] = time.time()

def getTimedoutInstances(instances, timeout):
    ret = set()
    for i, t in instances.iteritems():
        if (time.time() - t) > timeout:
            ret.add(i)

    return ret

@defer.inlineCallbacks
def terminateInstances(credentialName, instances, state):
    credClient = cred_client.CredentialClient(credentialName,
                                              state.mq,
                                              state.clustersState.conf)

    yield credClient.terminateInstances(instances)
                                              

def removeInstances(removeList, allInstances):
    for i in removeList:
        allInstances.pop(i)

@defer.inlineCallbacks
def getKnownInstances(credentialName):
    clusters = yield clusters_client.listClusters({}, 'guest')

    clustersOnCred = [cluster
                      for cluster in clusters
                      if cluster['cred_name'] == credentialName]

    knownInstances = set()
    for cluster in clustersOnCred:
        allClusterInstances = ([cluster['master']['instance_id']] +
                               [i['instance_id']
                                for i in cluster['exec_nodes']] +
                               [i['instance_id']
                                for i in cluster['data_nodes']])
        for i in allClusterInstances:
            knownInstances.add(i)

    defer.returnValue(knownInstances)
        
@defer.inlineCallbacks
def getOrphans(credentialName, state):
    @defer.inlineCallbacks
    def _sshAble(instance):
        sshUser = state.clustersState.machineConf('ssh.user')
        sshOptions = state.clustersState.machineConf('ssh.options')

        try:
            yield ssh.runProcessSSH(instance['public_dns'],
                                    'echo hello',
                                    None,
                                    None,
                                    sshUser,
                                    sshOptions)
        except:
            defer.returnValue(False)

        defer.returnValue(True)

    credClient = cred_client.CredentialClient(credentialName,
                                              state.mq,
                                              state.clustersState.conf)

    knownInstances = yield getKnownInstances(credentialName)

    instances = yield credClient.listInstances()

    instances = [i
                 for i in instances
                 if i['instance_id'] not in knownInstances]
    

    sshAble = yield defer_utils.mapPar(_sshAble, instances, parallel=5)

    ret = set([i['instance_id']
               for canSsh, i in zip(sshAble, instances)
               if canSsh])

    defer.returnValue(ret)
    

@defer_utils.timeIt
@defer.inlineCallbacks
def updateOrphanInfo(state):
    try:
        credentials = yield cred_client.listCredentials()
        credentials = [c['name'] for c in credentials]
        
        for credential in credentials:
            orphanedInstances = yield getOrphans(credential, state)
            log.msg('ORPHANS: Found %s' % (', '.join(orphanedInstances),))
            credInstances = state.orphanedInstances.setdefault(credential, {})
            removeAdopted(credInstances, orphanedInstances)
            updateOrphans(credInstances, orphanedInstances)


        for credential, instances in state.orphanedInstances.iteritems():
            timedoutInstances = getTimedoutInstances(instances, INSTANCE_TIMEOUT)
            if timedoutInstances:
                log.msg('ORPHANS: %s' % (', '.join(timedoutInstances),))
                #yield terminateInstances(credential,
                #                         timedoutInstances.keys(),
                #                         state)

            removeInstances(timedoutInstances.keys(), instances)
    except Exception, err:
        log.err('ORPHANS: Failed')
        log.err(err)

    reactor.callLater(REFRESH_FREQUENCY, updateOrphanInfo, state)

def subscribe(mq, state):
    reactor.callLater(0.0, updateOrphanInfo, State(state, mq))

import os

from twisted.internet import defer

from twisted.python import log

from igs.utils import config
from igs.utils import functional as func

from igs_tx.utils import defer_utils
from igs_tx.utils import global_state
from igs_tx.utils import ssh
from igs_tx.utils import defer_pipe

from vappio.tasks import task

from vappio.instance import config as vappio_config

from vappio_tx.clusters import persist

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.www_client import clusters as clusters_client_www
from vappio_tx.www_client import credentials as credentials_client_www

RUN_INSTANCE_TRIES = 4

WAIT_FOR_STATE_TRIES = 50

WAIT_FOR_SSH_TRIES = 10

WAIT_FOR_SERVICE_TRIES = 3

WAIT_FOR_BOOT_TRIES = 120

class Error(Exception):
    pass

class MasterError(Exception):
    pass

def saveCluster(cl, state):
    state.clustersCache[(cl.clusterName, cl.userName)] = cl
    saved = persist.saveCluster(cl)
    saved.addCallback(lambda _ : cl)
    return saved


@defer.inlineCallbacks
def startMaster(state, credClient, taskName, cl):
    def _updatePState(pState, instances):
        if instances:
            cl = pState.cluster.setMaster(instances[0])
            pState = pState.update(cluster=cl,
                                   instances=instances)
            return saveCluster(pState.cluster, pState.state).addCallback(lambda _ : pState)
        else:
            cl = pState.cluster.setState(pState.cluster.FAILED)
            def _raise(_):
                raise MasterError('Could not start master')
            return saveCluster(cl, pState.state).addCallback(_raise)

    @defer.inlineCallbacks
    def _waitForInstances(pState, tries, f, errMsg):
        instancesNew = yield retryAndTerminateDeferred(pState.credClient,
                                                       tries,
                                                       pState.instances,
                                                       f)

        yield tasks_tx.updateTask(pState.taskName,
                                  lambda t : t.progress())
        
        if len(instancesNew) != len(pState.instances):
            yield tasks_tx.updateTask(pState.taskName, lambda t : t.addMessage(task.MSG_ERROR, errMsg))

        defer.returnValue(pState)

    @defer.inlineCallbacks
    def _loadConfig(pState):
        credConfig = yield credClient.credentialConfig()
        cluster = pState.cluster.update(config=config.configFromMap({'general.ctype': credConfig['general.ctype']},
                                                                    base=config.configFromConfig(pState.cluster.config,
                                                                                                 base=config.configFromMap(credConfig))))
        pState = pState.update(cluster=cluster)
        defer.returnValue(pState)    

    @defer.inlineCallbacks
    def _waitForClusterInfo(pState):
        def _isClusterInfoResponding(instance):
            return clusters_client_www.listClusters(instance['public_dns'],
                                                   'local',
                                                   'guest').addCallback(lambda _: True).addErrback(lambda _: False)

        pState = yield _waitForInstances(pState, 
                                         WAIT_FOR_SERVICE_TRIES, 
                                         _isClusterInfoResponding, 
                                         "Cluster Info WS not responding.")
        
        defer.returnValue(pState)

    @defer.inlineCallbacks
    def _waitForCredentialsList(pState):
        def _isCredentialsListResponding(instance):
            return credentials_client_www.listCredentials(instance['public_dns'],
                                                         'local').addCallback(lambda _: True).addErrback(lambda _: False)

        pState = yield _waitForInstances(pState, 
                                         WAIT_FOR_SERVICE_TRIES, 
                                         _isCredentialsListResponding, 
                                         "Credentials List WS not responding.")
        
        defer.returnValue(pState)

    @defer.inlineCallbacks
    def _startMaster(pState):
        mode = [vappio_config.MASTER_NODE]
        masterConf = vappio_config.createDataFile(pState.cluster.config,
                                                  mode,
                                                  outFile='/tmp/machine.' + global_state.make_ref() + '.conf')

        dataFile = vappio_config.createMasterDataFile(pState.cluster, masterConf)

        master = yield runInstancesWithRetry(credClient,
                                             pState.cluster.config('cluster.ami'),
                                             pState.cluster.config('cluster.key'),
                                             pState.cluster.config('cluster.master_type'),
                                             pState.cluster.config('cluster.master_groups'),
                                             pState.cluster.config('cluster.availability_zone', default=None),
                                             pState.cluster.config('cluster.master_bid_price', default=None),
                                             1,
                                             open(dataFile).read())
        pState = yield _updatePState(pState, master)

        os.remove(masterConf)
        os.remove(dataFile)

        yield tasks_tx.updateTask(taskName,
                                  lambda t : t.addMessage(task.MSG_SILENT,
                                                          'Master started').progress())
        defer.returnValue(pState)


    
    # This state object is what will be threaded through all
    # of our callbacks
    pState = func.Record(state=state,
                         cluster=cl,
                         credClient=credClient,
                         taskName=taskName)

    yield tasks_tx.updateTask(taskName,
                              lambda t : t.update(numTasks=t.numTasks + 8))
    

    try:
        yield tasks_tx.updateTask(taskName,
                                  lambda t : t.addMessage(task.MSG_SILENT,
                                                          'Starting master for ' + pState.cluster.clusterName).progress())

        yield saveCluster(pState.cluster, pState.state)

        pState = yield _loadConfig(pState)
        pState = yield _startMaster(pState)
        pState = yield waitForInstances(pState, _updatePState)

        pState = yield defer_pipe.pipe([_waitForClusterInfo,
                                        _waitForCredentialsList])(pState)

        pState = pState.update(cluster=pState.cluster.setState(pState.cluster.RUNNING))
        yield saveCluster(pState.cluster, pState.state)
    except Exception, err:
        # Doing it this way because deferred inlines aren't *completely* legit,
        # in that I cannot yield anything in an except block without losing my stacktrace
        # on the reraise.  So I'm doing this call-back style and raising.  There IS a
        # possible race here where what if the raise causes the entire program to terminate?
        # If so we cannot gurantee that the FAILED state will actually be set. But given how
        # vappio is setup, this seems unlikely to happen
        persist.loadCluster(cl.clusterName, cl.userName
                            ).addCallback(lambda cluster : saveCluster(cluster.setState(cluster.FAILED), state))
        raise

    defer.returnValue(pState.cluster)


@defer.inlineCallbacks
def startExecNodes(state, credClient, taskName, numExec, cl):
    def _updatePState(pState, instances):
        cl = pState.cluster.update(execNodes=instances)
        pState = pState.update(cluster=cl,
                               instances=instances)
        return saveCluster(pState.cluster, pState.state).addCallback(lambda _ : pState)
    
    @defer.inlineCallbacks
    def _createDataFilesAndStartExec(pState):
        dataFile = vappio_config.createExecDataFile(pState.cluster.config, pState.cluster.master, '/tmp/machine.conf')
        instances = yield runInstancesWithRetry(pState.credClient,
                                                pState.cluster.config('cluster.ami'),
                                                pState.cluster.config('cluster.key'),
                                                pState.cluster.config('cluster.exec_type'),
                                                pState.cluster.config('cluster.exec_groups'),
                                                pState.cluster.config('cluster.availability_zone', default=None),
                                                pState.cluster.config('cluster.exec_bid_price', default=None),
                                                numExec,
                                                open(dataFile).read())
        yield tasks_tx.updateTask(taskName,
                                  lambda t : t.addMessage(task.MSG_SILENT,
                                                          'Started %d instances' % len(instances)).progress())

        # We want to combine the instnaces we just created with the ones there already, this just
        # makes it a bit easier to deal with later on.
        pState = yield _updatePState(pState, instances + pState.cluster.execNodes)
        os.remove(dataFile)
        defer.returnValue(pState)

    
    # This state object is what will be threaded through all
    # of our callbacks
    pState = func.Record(state=state,
                         cluster=cl,
                         credClient=credClient,
                         taskName=taskName)

    def _updateTask(t):
        t = t.addMessage(task.MSG_SILENT,
                         'Adding %d instances to %s' % (numExec, pState.cluster.clusterName))
        t = t.progress()
        t = t.update(numTasks=t.numTasks + 5)
        return t
    
    yield tasks_tx.updateTask(taskName,
                              _updateTask)

    
    pState = yield _createDataFilesAndStartExec(pState)
    pState = yield waitForInstances(pState, _updatePState)

    
    defer.returnValue(pState.cluster)

@defer.inlineCallbacks
def waitForInstances(pState, updateF):
    @defer.inlineCallbacks
    def _waitForState(pState):
        instancesNew = yield retryAndTerminate(pState.credClient,
                                               WAIT_FOR_STATE_TRIES,
                                               pState.instances,
                                               lambda i : i['state'] == 'running')

        yield tasks_tx.updateTask(pState.taskName,
                                  lambda t : t.progress())
        if len(instancesNew) != len(pState.instances):
            yield tasks_tx.updateTask(pState.taskName,
                                      lambda t : t.addMessage(task.MSG_ERROR,
                                                              'Not all instances started: %d' % len(instancesNew)))

        pState = yield updateF(pState, instancesNew)
        defer.returnValue(pState)
                

    @defer.inlineCallbacks
    def _waitForInstances(pState, tries, f, errMsg):
        instancesNew = yield retryAndTerminateDeferred(pState.credClient,
                                                       tries,
                                                       pState.instances,
                                                       f)

        yield tasks_tx.updateTask(pState.taskName,
                                  lambda t : t.progress())
        
        if len(instancesNew) != len(pState.instances):
            yield tasks_tx.updateTask(pState.taskName, lambda t : t.addMessage(task.MSG_ERROR, errMsg))

        pState = yield updateF(pState, instancesNew)
        defer.returnValue(pState)

    @defer.inlineCallbacks
    def _waitForSSH(pState):
        def _isInstanceUp(i):
            return ssh.runProcessSSH(i['public_dns'],
                                     'echo hello',
                                     None,
                                     None,
                                     pState.cluster.config('ssh.user'),
                                     pState.cluster.config('ssh.options')
                                     ).addCallback(lambda _ : True).addErrback(lambda _ : False)

        pState = yield _waitForInstances(pState,
                                         WAIT_FOR_SSH_TRIES,
                                         _isInstanceUp,
                                         'Some instances did not respond to SSH')

        defer.returnValue(pState)

    @defer.inlineCallbacks
    def _waitForRemoteBoot(pState):
        def _isBootComplete(i):
            return ssh.runProcessSSH(i['public_dns'],
                                     'test -e /tmp/startup_complete',
                                     None,
                                     None,
                                     pState.cluster.config('ssh.user'),
                                     pState.cluster.config('ssh.options')
                                     ).addCallback(lambda _ : True).addErrback(lambda _ : False)            

        pState = yield _waitForInstances(pState,
                                         WAIT_FOR_BOOT_TRIES,
                                         _isBootComplete,
                                         'Some instances did not boot up')
        
        defer.returnValue(pState)
    
    pState = yield defer_pipe.pipe([_waitForState,
                                    _waitForSSH,
                                    _waitForRemoteBoot])(pState)

    defer.returnValue(pState)


def runInstancesWithRetry(credClient,
                          ami,
                          key,
                          iType,
                          groups,
                          availZone,
                          bidPrice,
                          numInstances,
                          userData):

    def _runInstances(num):
        if bidPrice:
            return credClient.runSpotInstances(bidPrice=bidPrice,
                                               ami=ami,
                                               key=key,
                                               instanceType=iType,
                                               groups=groups,
                                               availabilityZone=availZone,
                                               numInstances=num,
                                               userData=userData)
        else:
            return credClient.runInstances(ami=ami,
                                           key=key,
                                           instanceType=iType,
                                           groups=groups,
                                           availabilityZone=availZone,
                                           numInstances=num,
                                           userData=userData)

        

    groups = [g.strip() for g in groups.split(',')]

    # Since defer_utils.tryUntil is stateless, we want to encode
    # some state for our function to use
    retryState = dict(desired_instances=numInstances,
                      instances=[])


    def _startInstances(retryState):
        runDefer = _runInstances(retryState['desired_instances'])

        def _onFailure(f):
            if retryState['desired_instances'] <= 1:
                retryState['desired_instances'] = 1
            else:
                retryState['desired_instances'] -= 1
            return f

        runDefer.addErrback(_onFailure)
        runDefer.addCallback(lambda i : retryState['instances'].extend(i))

        def _ensureAllInstances(_):
            if len(retryState['instances']) < retryState['desired_instances']:
                retryState['desired_instances'] = retryState['desired_instances'] - len(retryState['instances'])
                raise Exception('Wanted %d instances, started %d, retrying' % (retryState['desired_instances'],
                                                                               len(retryState['instances'])))

        runDefer.addCallback(_ensureAllInstances)
        
        runDefer.addCallback(lambda _ : retryState['instances'])


        return runDefer
    
    runAndRetry = defer_utils.tryUntil(RUN_INSTANCE_TRIES,
                                       lambda : _startInstances(retryState),
                                       onFailure=defer_utils.sleep(30))


    def _failIfNoneStarted(f):
        if not len(retryState['instances']):
            return f
        else:
            return retryState['instances']

    runAndRetry.addErrback(_failIfNoneStarted)
    return runAndRetry

def retryAndTerminateDeferred(credClient, retries, instances, f):
    """
    f does return a deferred.
    
    f is called on every instance in instances.  If any calls
    return False, the instance list is updated after INSTANCE_REFRESH_RATE
    seconds have passed and repeated.  If 'retries' attempts have been done and
    failed, all those instances which returned False are terminated.
    """
    def tryF():
        updateDefer = credClient.updateInstances(instances)
        updateDefer.addCallback(lambda instances : defer_utils.mapSerial(f, instances))

        def _failIfNotAnyFailed(res):
            #
            # If all calls to f succeeded then simply return an updated list of instances
            # otherwise sleep for awhile and return failure and surrounding code will rerun or fail out
            if all(res):
                return credClient.updateInstances(instances)
            else:
                raise Exception('Not all instances succeded')

        updateDefer.addCallback(_failIfNotAnyFailed)

        return updateDefer
        
    retryDefer = defer_utils.tryUntil(retries, tryF, onFailure=defer_utils.sleep(30))

    def _terminateBad(fail):
        log.err(fail)
        
        updateDefer = credClient.updateInstances(instances)
        updateDefer.addCallback(lambda instances : defer_utils.mapSerial(f, instances).addCallback(lambda r : zip(instances, r)))
        
        def _partition(resInstances):
            log.msg(resInstances)
            badInstances = [i for i, r in resInstances if not r]
            goodInstances = [i for i, r in resInstances if r]
            
            terminateDefer = credClient.terminateInstances(badInstances)
            terminateDefer.addCallback(lambda _ : goodInstances)
            return terminateDefer

        updateDefer.addCallback(_partition)
        return updateDefer

    retryDefer.addErrback(_terminateBad)
    
    return retryDefer

def retryAndTerminate(credClient, retries, instances, f):
    return retryAndTerminateDeferred(credClient, retries, instances, lambda i : defer.succeed(f(i)))

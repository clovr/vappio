##
# These functions allow you to do things with clusters.
# A lot of the functionality is wrapped in a Cluster object
import time
import os
import json

from twisted.python.reflect import fullyQualifiedName, namedAny

from igs.utils.commands import runSystemEx, runCommandGens
from igs.utils.ssh import scpToEx, runSystemSSHEx, runSystemSSH
from igs.utils.logging import errorPrintS, errorPrint, DEBUG
from igs.utils.functional import applyIfCallable
from igs.utils.errors import TryError
from igs.utils.config import configFromMap

from igs.threading.threads import runThreadWithChannel

from vappio.instance.config import createDataFile, createMasterDataFile, createExecDataFile, DEV_NODE, MASTER_NODE, EXEC_NODE, RELEASE_CUT
from vappio.instance.control import runSystemInstanceEx


NUM_TRIES = 50

class ClusterError(Exception):
    pass


class Cluster:
    """
    This represents a cluster
    """

    def __init__(self, name, ctype, config):
        self.name = name
        self.ctype = ctype
        self.config = config

        self.master = None
        self.execNodes = []
        self.dataNodes = []


    def setMaster(self, master):
        self.master = master

    def addExecNodes(self, execs):
        self.execNodes = updateDict(dict([(i.instanceId, i) for i in self.execNodes]),
                                    dict([(i.instanceId, i) for i in execs])).values()

    def addDataNodes(self, datas):
        self.dataNodes = updateDict(dict([(i.instanceId, i) for i in self.dataNodes]),
                                    dict([(i.instanceId, i) for i in datas])).values()                                        
        

def updateDict(d, nd):
    """
    Adds the key/values in nd to d and returns d
    """
    d.update(nd)
    return d


def clusterToDict(cluster):
    """
    Converts a cluster to a dict
    """
    return dict(name=cluster.name,
                ctype=fullyQualifiedName(cluster.ctype),
                config=json.dumps(dict([(k, cluster.config(k)) for k in cluster.config.keys()])),
                master=cluster.ctype.instanceToDict(cluster.master),
                execNodes=[cluster.ctype.instanceToDict(i) for i in cluster.execNodes],
                dataNodes=[cluster.ctype.instanceToDict(i) for i in cluster.dataNodes])

def clusterFromDict(d):
    """
    Loads a cluster from a dict
    """
    cluster = Cluster(d['name'], namedAny(d['ctype']), configFromMap(json.loads(d['config'])))
    cluster.setMaster(cluster.ctype.instanceFromDict(d['master']))
    cluster.addExecNodes([cluster.ctype.instanceFromDict(i) for i in d['execNodes']])
    cluster.addDataNodes([cluster.ctype.instanceFromDict(i) for i in d['dataNodes']])

    return cluster

def startCluster(cluster, numExec, reporter=None, devMode=False, releaseCut=False):
    startMaster(cluster, reporter, devMode, releaseCut)
    startExecNodes(cluster, numExec, reporter)
    return cluster
                
        
def startMaster(cluster, reporter=None, devMode=False, releaseCut=False):
    """
    This starts a master on the given cluster and
    returns the cluster with the master value set.

    reporter is a function that gets called at various points with the master.
    The master is passed as a list with 1 element
    
    This mutates the cluster object
    """

    mode = [MASTER_NODE]
    if devMode: mode.append(DEV_NODE)
    if releaseCut: mode.append(RELEASE_CUT)

    masterConf = createDataFile(cluster.config,
                                mode,
                                outFile='/tmp/machine.tmp.conf')
    
    dataFile = createMasterDataFile(cluster.config, masterConf, os.getenv('EC2_CERT'), os.getenv('EC2_PRIVATE_KEY'))

    os.remove(masterConf)

    master = runInstancesWithRetry(cluster.ctype,
                                   cluster.config('cluster.ami'),
                                   cluster.config('cluster.key'),
                                   cluster.config('cluster.master_type'),
                                   cluster.config('cluster.master_groups'),
                                   cluster.config('cluster.availability_zone', default=None),
                                   1,
                                   dataFile)[0]

    applyIfCallable(reporter, [master])

    master = runAndTerminateBad(cluster,
                                lambda : waitForState(cluster.ctype,
                                                      NUM_TRIES,
                                                      [master],
                                                      cluster.ctype.Instance.RUNNING,
                                                      reporter))[0]
    applyIfCallable(reporter, [master])
    
    master = runAndTerminateBad(cluster,
                                lambda : waitForSSHUp(cluster.config, NUM_TRIES, [master]))[0]

    cluster.setMaster(master)


    return cluster
    

def startExecNodes(cluster, numExec, reporter=None):
    """
    This starts a number of exec nodes.  It will add them to the cluster
    and returnst he cluster

    It is valid to give 0 for numExec.
    """

    ##
    # Function body
    if numExec:

        dataFile = createExecDataFile(cluster.config, cluster.master, '/tmp/machine.conf')

        slaves = runAndTerminateBad(cluster,
                                    lambda : runInstancesWithRetry(cluster.ctype,
                                                                   cluster.config('cluster.ami'),
                                                                   cluster.config('cluster.key'),
                                                                   cluster.config('cluster.exec_type'),
                                                                   cluster.config('cluster.exec_groups'),
                                                                   cluster.config('cluster.availability_zone', default=None),
                                                                   numExec,
                                                                   dataFile))

        applyIfCallable(reporter, slaves)



        ##
        # This could be a problem in the future.  This waits for ALL of them to reach the given
        # state but what if 1 machine takes 10 minutes to start and the rest are already started?
        # Those other machines could be getting work and through SGE and the rest of the setup
        # for a node is not complete yet.
        #
        # In the future, all node setup should probably happen through the datafile scrip that is uploaded.
        # Alternatively, we can stream waitForState and have return nodes as they reach the state.
        slaves = runAndTerminateBad(cluster,
                                    lambda : waitForState(cluster.ctype,
                                                          NUM_TRIES,
                                                          slaves,
                                                          cluster.ctype.Instance.RUNNING,
                                                          reporter))
                
        applyIfCallable(reporter, slaves)
        slaves = runAndTerminateBad(cluster,
                                    lambda: waitForSSHUp(cluster.config,
                                                         NUM_TRIES,
                                                         slaves))

        
        cluster.addExecNodes(slaves)
        if len(slaves) != numExec:
            raise TryError('Unable to bring up all nodes', cluster)
                
        return cluster

        
def terminateCluster(cluster):
    cluster.ctype.terminateInstances([cluster.master] + cluster.execNodes + cluster.dataNodes)

def waitForState(ctype, tries, instances, wantState, reporter):
    """
    reporter can be None if one doesn't want to report anything
    """
    def _matchState(instances):
        for i in instances:
            if i.state != wantState:
                return False

        return True
    
    while tries > 0:
        ##
        # EC2 has been doing this annoying thing where you run an instance
        # but it doesn't show up in ec2-describe-images for a few minutes
        # We will handle this by making sure the length of previous instance and
        # this instance match, and if not
        instancesPrime = ctype.updateInstances(instances)
        if len(instancesPrime) == len(instances):
            instances = instancesPrime
        applyIfCallable(reporter, instances)
        if _matchState(instances):
            return instances
        else:
            tries -= 1
            time.sleep(30)

    
    raise TryError('Not all instances reached state: ' + wantState, ([i for i in instances if i.state == wantState],
                                                                     [i for i in instances if i.state != wantState]))


def waitForSSHUp(conf, tries, instances):
    def _wrapCheckSSHUp(chan):
        instance, rchan = chan.receive()
        try:
            rchan.send(_checkSSHUp(instance))
        except Exception, err:
            errorPrint("Exception thrown: " + str(err))
            rchan.sendError(err)
            
    def _checkSSHUp(i):
        return runSystemSSH(i.publicDNS,
                            'echo hello',
                            None,
                            None,
                            conf('ssh.user'),
                            conf('ssh.options'),
                            log=DEBUG)
        
    def _sshTest(res):
        return all(c == 0 for c in res)

    while tries > 0:
        chans = [runThreadWithChannel(_wrapCheckSSHUp)[1].sendWithChannel(i)
                 for i in instances]
        res = [c.receive() for c in chans]
        if _sshTest(res):
            return instances
        else:
            time.sleep(30)
            tries -= 1

    raise TryError('SSH did not come up on all instances', ([i for c, i in zip(instances, res) if c == 0],
                                                            [i for c, i in zip(instances, res) if c != 0]))


def runInstancesWithRetry(ctype, ami, key, itype, groups, availzone, num, dataFile):
    """
    Tries to start up N instances, will try to run more if it cannot bring up all

    TODO: Modify this so it only tries N times and throws a TryError if it fails
    """
    instances = ctype.runInstances(ami,
                                   key,
                                   itype,
                                   groups,
                                   availzone,
                                   num,
                                   userDataFile=dataFile)
    if len(instances) < num:
        instances += runInstancesWithRetry(ctype,
                                           ami,
                                           key,
                                           itype,
                                           groups,
                                           availzone,
                                           num - len(instances),
                                           dataFile)

    return instances

def updateDirs(cluster, instances):
    def _updateDirs(chan):
        i, rchan = chan.receive()
        try:
            runSystemInstanceEx(i,
                                'updateAllDirs.py --vappio-py',
                                None,
                                errorPrintS,
                                user=cluster.config('ssh.user'),
                                options=cluster.config('ssh.options'),
                                log=DEBUG)
            runSystemInstanceEx(i,
                                'updateAllDirs.py --vappio-py --vappio-scripts --config_policies --clovr_pipelines --vappio-py-www',
                                None,
                                errorPrintS,
                                user=cluster.config('ssh.user'),
                                options=cluster.config('ssh.options'),
                                log=DEBUG)
            ##
            # Just send anything to know we are done
            rchan.send(True)
        except Exception, err:
            rchan.sendError(err)

    chans = [runThreadWithChannel(_updateDirs)[1].sendWithChannel(i)
             for i in instances]

    ##
    # Collect all threads
    for c in chans:
        c.receive()


def runCommandOnCluster(cluster, command, justMaster=False):
    """
    Runs a command on the cluster.  If justMaster is True (False by default), command
    is just run on the master
    """
    def _runCommandOnInstance(chan):
        i, rchan = chan.receive()
        try:
            runSystemInstanceEx(i,
                                command,
                                None,
                                errorPrintS,
                                user=cluster.config('ssh.user'),
                                options=cluster.config('ssh.options'),
                                log=True)
            rchan.send(True)
        except Exception, err:
            rchan.sendError(err)
            
    instances = [cluster.master]
    if not justMaster:
       instances += cluster.execNodes + cluster.dataNodes


    chans = [runThreadWithChannel(_runCommandOnInstance)[1].sendWithChannel(i)
             for i in instances]

    ##
    # Collect all threads
    for c in chans:
        c.receive()


def runAndTerminateBad(cluster, func):
    """
    This calls func and if a TryError is thrown
    it is assumed .result is a tuple containing
    (good, bad) list of instances.  The bad
    instances are terminated and the good ones are
    returned
    """
    try:
        return func()
    except TryError, err:
        slaves, bad = err.result
        cluster.ctype.terminateInstances(bad)
        return slaves
    

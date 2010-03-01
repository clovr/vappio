##
# These functions allow you to do things with clusters.
# A lot of the functionality is wrapped in a Cluster object
import time
import os
import json

from twisted.python.reflect import fullyQualifiedName, namedAny

from igs.utils.commands import runSystemEx, runCommandGens
from igs.utils.ssh import scpToEx, runSystemSSHEx, runSystemSSH
from igs.utils.logging import errorPrintS, errorPrint
from igs.utils.functional import applyIfCallable
from igs.utils.errors import TryError
from igs.utils.config import configFromMap

from igs.threading.threads import runThreadWithChannel

from vappio.instance.config import createDataFile, createMasterDataFile, createExecDataFile, DEV_NODE, MASTER_NODE, EXEC_NODE, RELEASE_CUT
from vappio.instance.control import runSystemInstanceEx


NUM_TRIES = 30

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

    dataFile = createMasterDataFile(cluster.config)

    master = runInstancesWithRetry(cluster.ctype,
                                   cluster.config('cluster.ami'),
                                   cluster.config('cluster.key'),
                                   cluster.config('cluster.master_type'),
                                   cluster.config('cluster.master_groups'),
                                   cluster.config('cluster.availability_zone', default=None),
                                   1,
                                   dataFile)[0]

    applyIfCallable(reporter, [master])

    master = waitForState(cluster.ctype,
                          NUM_TRIES,
                          [master],
                          cluster.ctype.Instance.RUNNING,
                          reporter)[0]

    applyIfCallable(reporter, [master])
    
    waitForSSHUp(cluster.config, NUM_TRIES, [master])

    os.remove(dataFile)

    dataFile = createDataFile(cluster.config,
                              mode,
                              master.privateDNS,
                              outFile='/tmp/machine.tmp.conf')
    scpToEx(master.publicDNS,
            dataFile,
            '/tmp/machine.conf',
            user=cluster.config('ssh.user'),
            options=cluster.config('ssh.options'))


    ##
    # Create and copy exec data file
    os.remove(dataFile)
    dataFile = createDataFile(cluster.config,
                              [EXEC_NODE],
                              master.privateDNS,
                              outFile='/tmp/machine.tmp.conf')
    
    scpToEx(master.publicDNS,
            dataFile,
            '/tmp/exec.machine.conf',
            user=cluster.config('ssh.user'),
            options=cluster.config('ssh.options'))

    os.remove(dataFile)
    ##
    # Copy up EC2 stuff
    scpToEx(master.publicDNS,
            os.getenv('EC2_CERT'),
            '/tmp/ec2-cert.pem',
            user=cluster.config('ssh.user'),
            options=cluster.config('ssh.options'))    

    scpToEx(master.publicDNS,
            os.getenv('EC2_PRIVATE_KEY'),
            '/tmp/ec2-pk.pem',
            user=cluster.config('ssh.user'),
            options=cluster.config('ssh.options'))    

    runSystemInstanceEx(master,
                        'chmod a+r /tmp/*.pem',
                        None,
                        errorPrintS,
                        user=cluster.config('ssh.user'),
                        options=cluster.config('ssh.options'),
                        log=True)
    
    if cluster.config('general.update_dirs'):
        updateDirs(cluster, [master])

    cluster.setMaster(master)

    try:
        runSystemInstanceEx(master,
                            'startUpNode.py',
                            None,
                            errorPrintS,
                            user=cluster.config('ssh.user'),
                            options=cluster.config('ssh.options'),
                            log=True)
    except Exception, err:
        raise TryError(err, cluster)

    return cluster
    

def startExecNodes(cluster, numExec, reporter=None):
    """
    This starts a number of exec nodes.  It will add them to the cluster
    and returnst he cluster

    It is valid to give 0 for numExec.
    """

    def _setupInstance(chan):
        i, rchan = chan.receive()
        try:
            try:
                scpToEx(i.publicDNS,
                        '/tmp/exec.machine.conf',
                        '/tmp/machine.conf',
                        user=cluster.config('ssh.user'),
                        options=cluster.config('ssh.options'))
            except:
                scpToEx(i.publicDNS,
                        '/tmp/exec.machine.conf',
                        '/tmp/machine.conf',
                        user=cluster.config('ssh.user'),
                        options=cluster.config('ssh.options'))

            if cluster.config('general.update_dirs'):
                updateDirs(cluster, [i])

            runSystemInstanceEx(i,
                                'startUpNode.py',
                                None,
                                errorPrintS,
                                user=cluster.config('ssh.user'),
                                options=cluster.config('ssh.options'),
                                log=True)
            ##
            # Just send something to let it know we are done
            rchan.send(True)
        except Exception, err:
            rchan.sendError(err)

    ##
    # Function body
    if numExec:
        dataFile = createExecDataFile(cluster.config, cluster.master)

        try:
            slaves = runInstancesWithRetry(cluster.ctype,
                                           cluster.config('cluster.ami'),
                                           cluster.config('cluster.key'),
                                           cluster.config('cluster.exec_type'),
                                           cluster.config('cluster.exec_groups'),
                                           cluster.config('cluster.availability_zone', default=None),
                                           numExec,
                                           dataFile)
        except TryError, err:
            ##
            # Weren't able to bring up all of them for some reason, but we got some
            slaves = err.result

        applyIfCallable(reporter, slaves)

        try:
            ##
            # This could be a problem in the future.  This waits for ALL of them to reach the given
            # state but what if 1 machine takes 10 minutes to start and the rest are already started?
            # Those other machines could be getting work and through SGE and the rest of the setup
            # for a node is not complete yet.
            #
            # In the future, all node setup should probably happen through the datafile scrip that is uploaded.
            # Alternatively, we can stream waitForState and have return nodes as they reach the state.
            try:
                slaves = waitForState(cluster.ctype,
                                      NUM_TRIES,
                                      slaves,
                                      cluster.ctype.Instance.RUNNING,
                                      reporter)
            except TryError, err:
                ##
                # Not all reached our state, but some of them hopefully did.  Take those that did and assign them to slaves
                # and terminate the rest
                #
                # This should be modified with some sort of error reporting, not sure how to do that yet though.
                slaves, bad = err.result
                cluster.ctype.terminateInstances(bad)
                
            applyIfCallable(reporter, slaves)
            try:
                waitForSSHUp(cluster.config,
                             NUM_TRIES,
                             slaves)
            except TryError, err:
                slaves, bad = err.result
                cluster.ctype.terminateInstances(bad)
                

            chans = [runThreadWithChannel(_setupInstance)[1].sendWithChannel(i)
                     for i in slaves]

            res = []
            ##
            # Clean up threads, collecting any errors
            for c, i in zip(chans, slaves):
                try:
                    c.receive()
                    res.append(i)
                except Exception, err:
                    errorPrint('Exception here?: ' + str(err))

            slaves = res


            cluster.addExecNodes(slaves)
            if len(slaves) != numExec:
                raise TryError('Unable to bring up all nodes', cluster)
                
            return cluster
        finally:
            #os.remove(dataFile)
            pass

        
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
                            log=True)
        
    def _sshTest(res):
        return all(c == 0 for c in res)

    while tries > 0:
        chans = [runThreadWithChannel(_wrapCheckSSHUp)[1].sendWithChannel(i)
                 for i in instances]
        res = [c.receive() for c in chans]
        if _sshTest(res):
            return
        else:
            time.sleep(30)
            tries -= 1

    raise TryError('SSH did not come up on all instances', ([i for c, i in zip(instances, res) if c == 0],
                                                            [i for c, i in zip(instances, res) if c != 0]))


def runInstancesWithRetry(ctype, ami, key, itype, groups, availzone, num, dataFile):
    """
    Tries to start up N instances, will try to run more if it cannot bring up all
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
                                log=True)
            runSystemInstanceEx(i,
                                'updateAllDirs.py --vappio-py --vappio-scripts --config_policies --clovr_pipelines --vappio-py-www',
                                None,
                                errorPrintS,
                                user=cluster.config('ssh.user'),
                                options=cluster.config('ssh.options'),
                                log=True)
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

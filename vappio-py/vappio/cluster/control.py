##
# These functions allow you to do things with clusters.
# A lot of the functionality is wrapped in a Cluster object
import time
import os
import json
import socket

from igs.utils import commands
from igs.utils import ssh
from igs.utils import logging
from igs.utils import functional
from igs.utils.errors import TryError
from igs.utils.config import configFromMap

from igs.threading.threads import runThreadWithChannel

from igs.cgi.request import performQuery

from vappio.instance.config import createDataFile, createMasterDataFile, createExecDataFile, MASTER_NODE
from vappio.instance.control import runSystemInstanceEx

from vappio.cluster import persist_mongo
from vappio.credentials import manager


NUM_TRIES = 150

CLUSTERINFO_URL = '/vappio/clusterInfo_ws.py'

class ClusterError(Exception):
    pass



def wrapReporter(reporter):
    def _(cluster):
        try:
            functional.applyIfCallable(reporter, cluster)
            return True
        except:
            return False

    return _

class Cluster(functional.Record):
    """
    This represents a cluster
    """

    def __init__(self, name, cred, config):
        self.name = name
        self.cred = cred
        self.ctype = cred.ctype
        self.config = config

        self.master = None
        self.execNodes = []
        self.dataNodes = []

        (self.config, self.credInst) = cred.ctype.instantiateCredential(self.config, self.cred)

        functional.Record.__init__(self)
        

    def setMaster(self, master):
        return self.update(master=master)

    def addExecNodes(self, execs):
        return self.update(execNodes=_combineInstances(self.execNodes, execs))


    def addDataNodes(self, datas):
        return self.update(dataNodes=_combineInstances(self.dataNodes, datas))


    def startCluster(self, numExec, reporter=None):
        return self.startMaster(reporter).startExecNodes(numExec, reporter)


    
    def startMaster(self, reporter=None):
        """
        This starts a master on the given cluster and
        returns the cluster with the master value set.
        
        reporter is a function that gets called at various points with the master.
        The master is passed as a list with 1 element
        
        This mutates the cluster object
        """

        reporterW = wrapReporter(reporter)
        mode = [MASTER_NODE]

        masterConf = createDataFile(self.config,
                                    mode,
                                    outFile='/tmp/machine.' + str(time.time()) + '-' + str(os.getpid()) + '.conf')
    
        dataFile = createMasterDataFile(self, masterConf)

        os.remove(masterConf)

        master = runInstancesWithRetry(self,
                                       self.config('cluster.ami'),
                                       self.config('cluster.key'),
                                       self.config('cluster.master_type'),
                                       self.config('cluster.master_groups'),
                                       self.config('cluster.availability_zone', default=None),
                                       self.config('cluster.master_bid_price', default=None),
                                       1,
                                       dataFile)[0]

        reporterW(self.setMaster(master))

        master = runAndTerminateBad(self,
                                    lambda : waitForState(self,
                                                          NUM_TRIES,
                                                          [master],
                                                          self.ctype.Instance.RUNNING,
                                                          reporterW))[0]
        reporterW(self.setMaster(master))
    
        master = runAndTerminateBad(self,
                                    lambda : waitForSSHUp(self.config, NUM_TRIES, [master]))[0]


        master = runAndTerminateBad(self,
                                    lambda : waitForInstancesReady(self.config, NUM_TRIES, [master]))[0]


        # Wait for Mongo to finish coming up
        count = NUM_TRIES
        while count > 0:
            try:
                loadCluster(self.name)
                return self.setMaster(master)
            except:
                count -= 1
                time.sleep(30)

        raise TryError('Unable to load the cluster remotely, something likely failed during startup', self)


    def startExecNodes(self, numExec, reporter=None):
        """
        This starts a number of exec nodes.  It will add them to the cluster
        and returnst he cluster
        
        It is valid to give 0 for numExec.
        """
        reporterW = wrapReporter(reporter)
        if numExec:
            dataFile = createExecDataFile(self.config, self.master, '/tmp/machine.conf')

            slaves = runAndTerminateBad(self,
                                        lambda : runInstancesWithRetry(self,
                                                                       self.config('cluster.ami'),
                                                                       self.config('cluster.key'),
                                                                       self.config('cluster.exec_type'),
                                                                       self.config('cluster.exec_groups'),
                                                                       self.config('cluster.availability_zone', default=None),
                                                                       self.config('cluster.exec_bid_price', default=None),
                                                                       numExec,
                                                                       dataFile))

            reporterW(self.addExecNodes(slaves))



            slaves = runAndTerminateBad(self,
                                        lambda : waitForState(self,
                                                              NUM_TRIES,
                                                              slaves,
                                                              self.ctype.Instance.RUNNING,
                                                              reporterW))
                
            reporterW(self.addExecNodes(slaves))
            slaves = runAndTerminateBad(self,
                                        lambda: waitForSSHUp(self.config,
                                                             NUM_TRIES,
                                                             slaves))


            slaves = runAndTerminateBad(self,
                                        lambda : waitForInstancesReady(self.config, NUM_TRIES, slaves))

            cluster = self.addExecNodes(slaves)
            if len(slaves) != numExec:
                raise TryError('Unable to bring up all nodes', cluster)
                
            return cluster
        else:
            return self
        

    def terminate(self):
        slaves = [i for i in self.execNodes + self.dataNodes if i.instanceId]
        if slaves:
            self.ctype.terminateInstances(self.credInst, slaves)
        if self.master.instanceId:
            self.ctype.terminateInstances(self.credInst, [self.master])
        return self
        


def _combineInstances(orig, n):
    return functional.updateDict(functional.updateDict(dict([(i.instanceId, i) for i in orig if not i.spotRequestId]),
                                                       dict([(i.instanceId, i) for i in n if not i.spotRequestId])),
                                 functional.updateDict(dict([(i.spotRequestId, i) for i in orig if i.spotRequestId]),
                                                       dict([(i.spotRequestId, i) for i in n if i.spotRequestId]))).values()
    
def clusterToDict(cluster):
    """
    Converts a cluster to a dict
    """
    return dict(name=cluster.name,
                cred=cluster.cred.name,
                config=json.dumps(dict([(k, cluster.config(k)) for k in cluster.config.keys()])),
                master=cluster.ctype.instanceToDict(cluster.master),
                execNodes=[cluster.ctype.instanceToDict(i) for i in cluster.execNodes],
                dataNodes=[cluster.ctype.instanceToDict(i) for i in cluster.dataNodes])

def clusterFromDict(d):
    """
    Loads a cluster from a dict
    """
    cluster = Cluster(d['name'], manager.loadCredential(d['cred']), configFromMap(json.loads(d['config'])))
    return cluster.setMaster(cluster.ctype.instanceFromDict(d['master'])
                             ).addExecNodes([cluster.ctype.instanceFromDict(i) for i in d['execNodes']]
                                            ).addDataNodes([cluster.ctype.instanceFromDict(i) for i in d['dataNodes']])

        


def loadCluster(name):
    cl = persist_mongo.load(name)
    cluster = clusterFromDict(cl)

    if name != 'local' and cluster.master.state == cluster.ctype.Instance.RUNNING:
        try:
            result = performQuery(cluster.master.publicDNS, CLUSTERINFO_URL, dict(name='local'), timeout=10)
            cluster = cluster.addExecNodes([cluster.ctype.instanceFromDict(i) for i in result['execNodes']])
            cluster = cluster.addDataNodes([cluster.ctype.instanceFromDict(i) for i in result['dataNodes']])
        except socket.timeout:
            raise persist_mongo.ClusterLoadIncompleteError('Failed to contact master when loading cluster', cluster)
        except Exception, err:
            raise persist_mongo.ClusterLoadIncompleteError(str(err), cluster)
        

    return cluster

def saveCluster(cluster):
    return persist_mongo.dump(clusterToDict(cluster))


def loadAllClusters():
    def _(n):
        try:
            return loadCluster(n)
        except persist_mongo.ClusterLoadIncompleteError, err:
            return err.cluster
        
    return [_(n) for n in persist_mongo.listClusters()]

def removeCluster(name):
    return persist_mongo.cleanUp(name)
    

def waitForState(cluster, tries, instances, wantState, reporterW):
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
        instancesPrime = cluster.ctype.updateInstances(cluster.credInst, instances)
        if len(instancesPrime) == len(instances):
            instances = instancesPrime
        reporterW(cluster.addExecNodes(instances))
        if _matchState(instances):
            return cluster.ctype.updateInstances(cluster.credInst, instances)
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
            logging.errorPrint("Exception thrown: " + str(err))
            rchan.sendError(err)
            
    def _checkSSHUp(i):
        return ssh.runSystemSSH(i.publicDNS,
                                'echo hello',
                                None,
                                None,
                                conf('ssh.user'),
                                conf('ssh.options'),
                                log=logging.DEBUG)
        
    def _sshTest(res):
        return all(c == 0 for c in res)

    while tries > 0:
        chans = [runThreadWithChannel(_wrapCheckSSHUp).channel.sendWithChannel(i)
                 for i in instances]
        res = [c.receive() for c in chans]
        if _sshTest(res):
            return instances
        else:
            time.sleep(30)
            tries -= 1

    raise TryError('SSH did not come up on all instances', ([i for c, i in zip(instances, res) if c == 0],
                                                            [i for c, i in zip(instances, res) if c != 0]))


def waitForInstancesReady(conf, tries, who):
    """
    This waits for an instance to be ready.
    Right now this just works on master nodes because it uses
    ClusterInfo.  In the future proper state will be setup in an instance
    so it will work anywhere
    """
    def _checkUp():
        try:
            for i in who:
                runSystemInstanceEx(i,
                                    'test -e /tmp/startup_complete',
                                    None,
                                    None,
                                    user=conf('ssh.user'),
                                    options=conf('ssh.options'),
                                    log=logging.DEBUG)
            return True
        except commands.ProgramRunError:
            return False

    try:
        functional.tryUntil(tries, lambda : time.sleep(30), _checkUp)
        return who
    except TryError:
        ##
        # If it failed, figure out who failed and throw a TryError
        good = []
        bad = []
        for i in who:
            try:
                runSystemInstanceEx(i,
                                    'test -e /tmp/startup_complete',
                                    None,
                                    None,
                                    user=conf('ssh.user'),
                                    options=conf('ssh.options'),
                                    log=logging.DEBUG)
                good.append(i)
            except commands.ProgramRunError:
                bad.append(i)

        raise TryError('Not all machines read', (good, bad))
    

def runInstancesWithRetry(cluster, ami, key, itype, groups, availzone, bidPrice, num, dataFile):
    """
    Tries to start up N instances, will try to run more if it cannot bring up all

    TODO: Modify this so it only tries N times and throws a TryError if it fails
    """
    if bidPrice is None:
        instances = cluster.ctype.runInstances(cluster.credInst,
                                               ami,
                                               key,
                                               itype,
                                               [g.strip() for g in groups.split(',')],
                                               availzone,
                                               num,
                                               userDataFile=dataFile)
    else:
        instances = cluster.ctype.runSpotInstances(cluster.credInst,
                                                   bidPrice,
                                                   ami,
                                                   key,
                                                   itype,
                                                   groups,
                                                   availzone,
                                                   num,
                                                   userDataFile=dataFile)
        
    if len(instances) < num:
        instances += runInstancesWithRetry(cluster,
                                           ami,
                                           key,
                                           itype,
                                           groups,
                                           availzone,
                                           bidPrice,
                                           num - len(instances),
                                           dataFile)

    return instances

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
        cluster.ctype.terminateInstances(cluster.credInst, bad)
        return slaves
    
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
                                lambda l : logging.logPrintS('%s : %s' % (i.publicDNS, l)),
                                logging.errorPrintS,
                                user=cluster.config('ssh.user'),
                                options=cluster.config('ssh.options'),
                                log=True)
            rchan.send(True)
        except Exception, err:
            rchan.sendError(err)
            
    instances = [cluster.master]
    if not justMaster:
        instances += cluster.execNodes + cluster.dataNodes


    chans = [runThreadWithChannel(_runCommandOnInstance).channel.sendWithChannel(i)
             for i in instances
             if i.state == cluster.ctype.Instance.RUNNING]

    # Collect all threads
    for c in chans:
        c.receive()

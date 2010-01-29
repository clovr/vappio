##
# These functions allow you to do things with clusters.
# A lot of the functionality is wrapped in a Cluster object
import time
import os

from igs.utils.commands import runSystemEx, runCommandGens
from igs.utils.ssh import scpToEx, runSystemSSHEx, runSystemSSHA, scpToA
from igs.utils.logging import errorPrintS

from vappio.instance.config import createDataFile, createMasterDataFile, createExecDataFile, DEV_NODE, MASTER_NODE, EXEC_NODE, RELEASE_CUT
from vappio.instance.control import runSystemInstanceEx, runSystemInstanceA


NUM_TRIES = 30


class TryError(Exception):
    pass

class ClusterError(Exception):
    pass

class Cluster:
    def __init__(self, name, ctype, config):
        """
        ctype is a reference to an object that implements the cluster interface
        for that type of cluster.  This can be a class or a module.
        """

        self.name = name
        self.ctype = ctype
        self.config = config

        self.master = None
        self.slaves = []


    def startCluster(self, numExec, devMode=False, releaseCut=False):
        """
        numExec - Number of exec nodes
        """

        self._startMaster(devMode, releaseCut)
        self.createExecs(numExec)


    def terminateCluster(self):
        self.ctype.terminateInstances([self.master] + self.slaves)


    def setMaster(self, master):
        """
        Sets the master to an instance
        """
        self.master = master

    def addExecs(self, execs):
        """
        Adds a list of exec nodes to the list this cluster manages
        """
        self.slaves.extend(execs)

    ##
    # some private methods
    def _startMaster(self, devMode, releaseCut):
        mode = [MASTER_NODE]
        if devMode: mode.append(DEV_NODE)
        if releaseCut: mode.append(RELEASE_CUT)
        
        dataFile = createMasterDataFile(self.config)

        master = runInstancesWithRetry(self.ctype,
                                       self.config('cluster.ami'),
                                       self.config('cluster.key'),
                                       self.config('cluster.master_type'),
                                       self.config('cluster.master_groups'),
                                       self.config('cluster.availability_zone'),
                                       1,
                                       dataFile)[0]
        
        
        master = waitForState(self.ctype, NUM_TRIES, [master], self.ctype.Instance.RUNNING)[0]
        waitForSSHUp(self.config, NUM_TRIES, [master])
        
        os.remove(dataFile)
        
        dataFile = createDataFile(self.config, mode, master.privateDNS)
        scpToEx(master.publicDNS, dataFile, '/tmp', user='root', options=self.config('ssh.options'))
        if self.config('general.update_dirs'):
            runSystemInstanceEx(master, 'updateAllDirs.py --vappio-py', None, errorPrintS, user='root', options=self.config('ssh.options'), log=True)
            runSystemInstanceEx(master, 'updateAllDirs.py --vappio-py --vappio-scripts --config_policies --clovr_pipelines', None, errorPrintS, user='root', options=self.config('ssh.options'), log=True)
        runSystemInstanceEx(master, 'startUpNode.py', None, errorPrintS, user='root', options=self.config('ssh.options'), log=True)
        
        os.remove(dataFile)

        self.setMaster(master)

    def createExecs(self, numExec, terminateOnFailure=True):
        def _setupInstance(i, dataFile):
            pr = scpToA(i.publicDNS, dataFile, '/tmp', user='root', options=self.config('ssh.options'))
            yield pr

            if pr.exitCode != 0:
                pr = scpToA(i.publicDNS, dataFile, '/tmp', user='root', options=self.config('ssh.options'))
                yield pr
                if pr.exitCode != 0:
                    raise ClusterError('Failed to start cluster on instance: ' + i.publicDNS)


            if self.config('general.update_dirs'):
                pr = runSystemInstanceA(i, 'updateAllDirs.py --vappio-py', None, errorPrintS, user='root', options=self.config('ssh.options'), log=True)
                yield pr

                if pr.exitCode != 0:
                    raise ClusterError('Failed to start cluster on instance: ' + i.publicDNS)

                pr = runSystemInstanceA(i, 'updateAllDirs.py --vappio-py --vappio-scripts --config_policies --clovr_pipelines', None, errorPrintS,
                                        user='root', options=self.config('ssh.options'), log=True)
                yield pr

                if pr.exitCode != 0:
                    raise ClusterError('Failed to start cluster on instance: ' + i.publicDNS)
            
                
            pr = runSystemInstanceA(i, 'startUpNode.py', None, errorPrintS, user='root', options=self.config('ssh.options'), log=True)
            yield pr

            if pr.exitCode != 0:
                raise ClusterError('Failed to start cluster on instance: ' + i.publicDNS)

        
        if numExec:
            dataFile = createExecDataFile(self.config, self.master)

            slaves = runInstancesWithRetry(self.ctype,
                                           self.config('cluster.ami'),
                                           self.config('cluster.key'),
                                           self.config('cluster.exec_type'),
                                           self.config('cluster.exec_groups'),
                                           self.config('cluster.availability_zone'),
                                           numExec,
                                           dataFile)
            
            
            try:
                slaves = waitForState(self.ctype, NUM_TRIES, slaves, self.ctype.Instance.RUNNING)
                ##
                # Lets manage these
                self.addExecs(slaves)
                
                waitForSSHUp(self.config, NUM_TRIES, slaves)
                
                dataFile = createDataFile(self.config, [EXEC_NODE], self.master.privateDNS)
                runCommandGens([_setupInstance(i, dataFile) for i in slaves])
#                 for i in slaves:
#                     scpToEx(i.publicDNS, dataFile, '/tmp', user='root', options=self.config('ssh.options'))
#                     #runSystemInstanceEx(i, 'updateAllDirs.py --vappio-py --vappio-scripts --config_policies', None, errorPrintS, user='root', options=self.config('ssh.options'), log=True)                    
#                     runSystemInstanceEx(i, 'startUpNode.py', None, errorPrintS, user='root', options=self.config('ssh.options'), log=True)
            except TryError:
                if terminateOnFailure:
                    self.terminateCluster()
                os.remove(dataFile)
                raise ClusterError('Could not start cluster')

            os.remove(dataFile)

        



def waitForState(ctype, tries, instances, wantState):
    def _matchState(instances):
        for i in instances:
            if i.state != wantState:
                return False

        return True
    
    while tries > 0:
        instances = ctype.updateInstances(instances)
        if _matchState(instances):
            return instances
        else:
            tries -= 1
            time.sleep(30)

    
    raise TryError('Not all instances reached state: ' + wantState)
            

def waitForSSHUp(conf, tries, instances):
    def _gen(pr):
        yield pr
        
    def _sshTest(instances):
        prs = [runSystemSSHA(i.publicDNS, 'echo hello', None, None, conf('ssh.user'), conf('ssh.options'), log=True)
               for i in instances]
        gens = [_gen(pr) for pr in prs]
        runCommandGens(gens)
        for pr in prs:
            if pr.exitCode != 0:
                return False

        return True

    while tries > 0:
        if _sshTest(instances):
            return
        else:
            time.sleep(30)
            tries -= 1

    raise TryError('SSH did not come up on all instances')

def runCommandOnCluster(cluster, command, justMaster=False):
    """
    Runs a command on the cluster.  If justMaster is True (False by default), command
    is just run on the master
    """
    def runCommandOnInstance(i, command):
        pr = runSystemInstanceA(i, command, None, errorPrintS,
                                user=cluster.config('ssh.user'), options=cluster.config('ssh.options'), log=True)
        yield pr

        if pr.exitCode != 0:
            raise ClusterError('Failed to run command on instance: ' + i.publicDNS)

    instances = [cluster.master]
    if not justMaster:
        instances += cluster.slaves
        
    runCommandGens([runCommandOnInstance(i, command) for i in instances])
    

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
        

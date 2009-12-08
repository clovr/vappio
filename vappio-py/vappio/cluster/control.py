##
# These functions allow you to do things with clusters.
# A lot of the functionality is wrapped in a Cluster object
import time
import os

from igs.utils.commands import runSystemEx, runCommandGens
from igs.utils.ssh import scpToEx, runSystemSSHEx, runSystemSSHA

from vappio.instance.config import createDataFile, DEV_NODE, MASTER_NODE, EXEC_NODE

NUM_TRIES = 20


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


    def startCluster(self, numExec, devMode=False):
        """
        numExec - Number of exec nodes
        """

        mode = [MASTER_NODE]
        if devMode: mode.append(DEV_NODE)
        
        dataFile = createDataFile(mode, '127.0.0.1')
                                  
        self.master = self.ctype.runInstances(self.config('cluster.ami'),
                                              self.config('cluster.key'),
                                              self.config('cluster.master_type'),
                                              self.config('cluster.master_groups'),
                                              self.config('cluster.availability_zone'),
                                              1,
                                              userDataFile=dataFile)[0]


        self.master = waitForState(self.ctype, NUM_TRIES, [self.master], self.ctype.Instance.RUNNING)[0]
        waitForSSHUp(self.config, NUM_TRIES, [self.master])
        scpToEx(self.master.publicDNS, dataFile, '/tmp', user='root', options=self.config('ssh.options'))
        runSystemSSHEx(self.master.publicDNS, 'startUpNode.py', None, None, user='root', options=self.config('ssh.options'))
        
        os.remove(dataFile)
                

        if numExec:
            dataFile = createDataFile([EXEC_NODE], self.master.publicDNS)

            self.slaves = self.ctype.runInstances(self.config('cluster.ami'),
                                                  self.config('cluster.key'),
                                                  self.config('cluster.exec_type'),
                                                  self.config('cluster.exec_groups'),
                                                  self.config('cluster.availability_zone'),
                                                  numExec,
                                                  userDataFile=dataFile)

        
            try:
                self.slaves = waitForState(self.ctype, NUM_TRIES, self.slaves, self.ctype.Instance.RUNNING)
                waitForSSHUp(self.config, NUM_TRIES, self.slaves)
                for i in self.slaves:
                    scpToEx(i.publicDNS, dataFile, '/tmp', user='root', options=self.config('ssh.options'))
                    runSystemSSHEx(i.publicDNS, 'startUpNode.py', None, None, user='root', options=self.config('ssh.options'))
            except TryError:
                self.terminateCluster()
                os.remove(dataFile)
                raise ClusterError('Could not start cluster')

            os.remove(dataFile)

        else:
            self.slaves = []


    def terminateCluster(self):
        self.ctype.terminateInstances([self.master] + self.slaves)



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
        prs = [runSystemSSHA(i.publicDNS, 'echo hello', None, None, 'root', conf('ssh.options'), log=True)
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
            tries -= 1

    raise TryError('SSH did not come up on all instances')

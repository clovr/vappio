##
# These functions allow you to do things with clusters.
# A lot of the functionality is wrapped in a Cluster object
import time
import os

from vappio.instance.config import createDataFile, DEV_NODE, MASTER_NODE, EXEC_NODE

NUM_TRIES = 20


class TryError(Exception):
    pass

class ClusterError(Exception):
    pass

class Cluster:
    def __init__(self, ctype, config):
        """
        ctype is a reference to an object that implements the cluster interface
        for that type of cluster.  This can be a class or a module.
        """

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
                                              numExec,
                                              userDataFile=dataFile)


        os.remove(dataFile)
        dataFile = createDataFile([EXEC_NODE], self.master.publicDNS)

        self.slaves = self.ctype.runInstances(self.config('cluster.ami'),
                                              self.config('cluster.key'),
                                              self.config('cluster.exec_type'),
                                              self.config('cluster.exec_groups'),
                                              self.config('cluster.availability_zone'),
                                              numExec,
                                              userDataFile=dataFile)

        os.remove(dataFile)
        
        try:
            self.slaves = waitForState(self.ctype, NUM_TRIES, self.slaves, self.ctype.Instance.RUNNING)
        except TryError:
            self.terminateCluster()
            raise ClusterError('Could not start cluster')


    def terminateCluster(self):
        self.ctype.terminateInstances([self.master] + self.slaves)



def waitForState(ctype, tries, instances, wantState):
    while tries > 0:
        instances = ctype.updateInstances(instances)
        for i in instances:
            if i.state != wantState:
                tries -= 1
                time.sleep(10)
                continue
        else:
            return instances

    
    raise TryError('Not all instances reached state: ' + wantState)
            

import json

import pymongo

from twisted.internet import threads

from igs.utils import functional as func
from igs.utils import config

class ClusterNotFoundError(Exception):
    def __init__(self, clusterName):
        self.clusterName = clusterName

    def __str__(self):
        return 'Cluster %s was not found' % self.clusterName

class Cluster(func.Record):
    """Simple representation for a cluster"""

    PENDING = 'pending'
    RUNNING = 'running'
    UNRESPONSIVE = 'unresponsive'
    TERMINATED = 'terminated'
    
    def __init__(self, clusterName, userName, credName, config):
        func.Record.__init__(self,
                             userName=userName,
                             clusterName=clusterName,
                             state=self.PENDING,
                             credName=credName,
                             config=config,
                             startTask=None,
                             addInstanceTasks=[],
                             execNodes=[],
                             dataNodes=[],
                             master=None)

    def setMaster(self, master):
        return self.update(master=master)

    def setState(self, state):
        return self.update(state=state)

    def addExecNodes(self, execNodes):
        return self.update(execNodes=self.execNodes + execNodes)

    def addDataNodes(self, dataNodes):
        return self.update(dataNodes=self.dataNodes + dataNodes)



def clusterToDict(cluster):
    return dict(user_name=cluster.userName,
                cluster_name=cluster.clusterName,
                state=cluster.state,
                cred_name=cluster.credName,
                config=config.configToDict(cluster.config),
                start_task=cluster.startTask,
                add_instance_tasks=cluster.addInstanceTasks,
                exec_nodes=cluster.execNodes,
                data_nodes=cluster.dataNodes,
                master=cluster.master)

def clusterFromDict(d):
    cl = Cluster(clusterName=d['cluster_name'],
                 userName=d['user_name'],
                 credName=d['cred_name'],
                 config=config.configFromMap(d['config']))
    return cl.setMaster(d['master']).setState(d['state']).addExecNodes(d['exec_nodes']).addDataNodes(d['data_nodes'])

def loadCluster(clusterName, userName):
    def _loadCluster():
        conn = pymongo.Connection()
        if clusterName == 'local':
            return conn.clovr.clusters.find_one(dict(cluster_name='local'))
        else:
            return conn.clovr.clusters.find_one(dict(cluster_name=clusterName, user_name=userName))

    d = threads.deferToThread(_loadCluster)
    
    def _checkForEmptyResponse(r):
        if r is None:
            raise ClusterNotFoundError(clusterName)
        return r

    d.addCallback(_checkForEmptyResponse)
    #
    # Conf needs to be converted to json when stored, so undo that
    d.addCallback(lambda c : clusterFromDict(func.updateDict(c, dict(config=json.loads(c['config'])))))
    return d

def loadAllClusters(userName):
    def _loadAllClusters():
        conn = pymongo.Connection()
        return list(conn.clovr.clusters.find(dict(user_name=userName))) + list(conn.clovr.clusters.find(dict(cluster_name='local')))

    d = threads.deferToThread(_loadAllClusters)

    def _convertFromDict(cls):
        return [clusterFromDict(func.updateDict(c, dict(config=json.loads(c['config']))))
                for c in cls]

    d.addCallback(_convertFromDict)
    return d

def loadClustersAdmin(clusterName=None):
    query = dict()
    if clusterName:
        query['cluster_name'] = clusterName

    d = threads.deferToThread(lambda : pymongo.Connection().clovr.clusters.find(query))
    def _convertFromDict(cls):
        return [clusterFromDict(func.updateDict(c, dict(config=json.loads(c['config']))))
                for c in cls]

    d.addCallback(_convertFromDict)
    return d

def saveCluster(cluster):
    if cluster.userName is None:
        userName = ''
    else:
        userName = str(cluster.userName)
    dc = func.updateDict(clusterToDict(cluster), dict(_id=cluster.clusterName + '-' + userName))
    dc['config'] = json.dumps(dc['config'])
    d = threads.deferToThread(lambda : pymongo.Connection().clovr.clusters.save(dc))

    return d

def removeCluster(cluster):
    return threads.deferToThread(lambda : pymongo.Connection().clovr.clusters.remove(dict(cluster_name=cluster.clusterName,
                                                                                          user_name=cluster.userName)))


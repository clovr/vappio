import json

import pymongo

from twisted.internet import defer
from twisted.internet import threads

from igs.utils import functional as func
from igs.utils import config
from igs.utils import dependency

class Error(Exception):
    pass

class ClusterNotFoundError(Error):
    def __init__(self, clusterName, userName):
        self.clusterName = clusterName
        self.userName = userName

    def __str__(self):
        return '(%s, %s)' % (self.clusterName, self.userName)

class TooManyClustersFoundError(ClusterNotFoundError):
    pass

class Cluster(func.Record):
    """Simple representation for a cluster"""

    PENDING = 'pending'
    RUNNING = 'running'
    UNRESPONSIVE = 'unresponsive'
    TERMINATED = 'terminated'
    FAILED = 'failed'
    
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
        execNodes = list(execNodes)
        instances = set([self._instanceId(i)
                         for i in execNodes])
        for i in self.execNodes:
            if self._instanceId(i) not in instances:
                execNodes.append(i)

        return self.update(execNodes=execNodes)

    def removeExecNodes(self, remExecNodes):
        remExecIds = set([self._instanceId(i)
                          for i in remExecNodes])
        
        execNodes = []
        
        for i in self.execNodes:
            if self._instanceId(i) not in remExecIds:
                execNodes.append(i)

        return self.update(execNodes=execNodes)

    def addDataNodes(self, dataNodes):
        return self.update(dataNodes=self.dataNodes + dataNodes)

    def removeDataNodes(self, remDataNodes):
        remDataIds = set([self._instanceId(i)
                          for i in remDataNodes])
        
        dataNodes = []
        
        for i in self.dataNodes:
            if self._instanceId(i) not in remDataIds:
                dataNodes.append(i)

        return self.update(dataNodes=dataNodes)
    
    def _instanceId(self, instance):
        return (instance['instance_id'], instance['spot_request_id'])


class ClusterPersistManager(dependency.Dependable):
    def __init__(self):
        dependency.Dependable.__init__(self)


    def clusterToDocument(self, cluster):
        return dict(user_name=cluster.userName,
                    cluster_name=cluster.clusterName,
                    state=cluster.state,
                    cred_name=cluster.credName,
                    config=json.dumps(config.configToDict(cluster.config)),
                    start_task=cluster.startTask,
                    add_instance_tasks=cluster.addInstanceTasks,
                    exec_nodes=cluster.execNodes,
                    data_nodes=cluster.dataNodes,
                    master=cluster.master)

    def clusterToDict(self, cluster):
        d = self.clusterToDocument(cluster)
        d['config'] = json.loads(d['config'])
        return d
    
    def clusterFromDocument(self, d):
        cl = Cluster(clusterName=d['cluster_name'],
                     userName=d['user_name'],
                     credName=d['cred_name'],
                     config=config.configFromMap(json.loads(d['config'])))
        cl = cl.setMaster(d['master'])
        cl = cl.setState(d['state'])
        cl = cl.addExecNodes(d['exec_nodes'])
        cl = cl.addDataNodes(d['data_nodes'])
        cl = cl.update(startTask=d['start_task'])
        return cl

    def clusterFromDict(self, d):
        d = dict(d)
        d['config'] = json.dumps(d['config'])
        return self.clusterFromDocument(d)

    @defer.inlineCallbacks
    def loadClustersByAdmin(self, criteria):
        def _loadCluster():
            conn = pymongo.Connection()
            return conn.clovr.clusters.find(criteria)

        clustersDoc = yield _loadCluster()
        clusters = map(self.clusterFromDocument, clustersDoc)
        
        self.changed('load', clusters)
        
        defer.returnValue(clusters)


    def loadClustersBy(self, criteria, userName):
        criteria = func.updateDict(criteria,
                                   {'user_name': {'$in': [userName, None]}})
        return self.loadClustersByAdmin(criteria)
        

    @defer.inlineCallbacks
    def loadCluster(self, clusterName, userName):
        clusters = yield self.loadClustersBy({'cluster_name': clusterName},
                                             userName)

        if not clusters:
            raise ClusterNotFoundError(clusterName, userName)
        elif len(clusters) > 1:
            raise TooManyClustersFoundError(clusterName, userName)
        else:
            defer.returnValue(clusters[0])

    @defer.inlineCallbacks
    def saveCluster(self, cluster):
        clusterDoc = self.clusterToDocument(cluster)

        def _saveCluster():
            userName = str(clusterDoc['user_name']) if clusterDoc['user_name'] else ''

            clusterDoc['_id'] = (clusterDoc['cluster_name'] +
                                 '_' +
                                 userName)
            return pymongo.Connection().clovr.clusters.save(clusterDoc,
                                                            safe=True)

        yield threads.deferToThread(_saveCluster)

        self.changed('save', cluster)

        defer.returnValue(cluster)

    @defer.inlineCallbacks
    def removeClustersByAdmin(self, criteria):
        """
        Removes a cluster by criteria.  We actually load
        all clusters that match the criteria prior to
        deleting so we can notify anyone that cares of
        which clusters got removed
        """
        def _removeCluster():
            clusters = pymongo.Connection().clovr.clusters
            return clusters.remove(criteria)

        clusters = yield self.loadClustersByAdmin(criteria)
        yield threads.deferToThread(_removeCluster)

        self.changed('remove', clusters)
        
        yield threads.deferToThread(_removeCluster)

        defer.returnValue(clusters)

    def removeClustersBy(self, criteria, userName):
        criteria = func.updateDict(criteria,
                                   {'user_name': userName})
        return self.removeClustersByAdmin(criteria)

    def removeCluster(self, clusterName, userName):
        return self.removeClustersBy({'cluster_name': clusterName},
                                     userName)
        


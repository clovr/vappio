import os

from twisted.internet import defer

from igs.utils import config
from igs.utils import functional as func

from igs_tx.utils import lock_manager
from igs_tx.utils import defer_utils

from vappio_tx.mq import client

from vappio_tx.internal_client import credentials as cred_client

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.clusters import persist

from vappio_tx.clusters import clusters_cleanup
from vappio_tx.clusters import cluster_refresh

from vappio_tx.clusters import cluster_mq_addinstances
from vappio_tx.clusters import cluster_mq_config
from vappio_tx.clusters import cluster_mq_list
from vappio_tx.clusters import cluster_mq_startcluster
from vappio_tx.clusters import cluster_mq_terminateinstances
from vappio_tx.clusters import cluster_mq_terminate



class State:
    """
    Maintain state information.  This should always be in a state in which
    it can be repopulated in case of a crash
    """

    def __init__(self, conf):
        self.conf = conf
        self.persistManager = persist.ClusterPersistManager()
        self.machineConf = config.configFromStream(open(conf('config.machine_conf')),
                                                   base=config.configFromEnv())
        self.clusterLocks = lock_manager.LockManager()
        self.unresponsiveClusters = {}
    
        

@defer_utils.timeIt
@defer.inlineCallbacks
def removeDeadClusters(mq, state):
    clusters = yield state.persistManager.loadClustersByAdmin({})

    clusters = [c for c in clusters if c.state in [c.FAILED, c.TERMINATED]]

    for c in clusters:
        credClient = cred_client.CredentialClient(c.credName,
                                                  mq,
                                                  state.conf)
        yield state.persistManager.deleteCluster(credClient,
                                                 c.clusterName,
                                                 c.userName)

@defer_utils.timeIt
@defer.inlineCallbacks
def loadLocalCluster(mq, state):
    """
    If local cluster is not present, load it
    """
    def _credential():
        if os.path.exists('/tmp/cred-info'):
            cert, pkey, ctype, metadata = open('/tmp/cred-info').read().split('\t')
            return {'name': 'local',
                    'desc': 'Local credential',
                    'ctype': ctype,
                    'cert': open(cert).read(),
                    'pkey': open(pkey).read(),
                    'metadata': metadata and dict([v.split('=', 1)
                                                   for v in metadata.split(',')]) or {},
                    'conf': config.configFromStream(open('/tmp/machine.conf'), lazy=True)}
        else:
            return {'name': 'local',
                    'desc': 'Local credential',
                    'ctype': 'local',
                    'cert': None,
                    'pkey': None,
                    'metadata': {},
                    'conf': config.configFromMap({})}
                                                  
    try:
        cluster = yield state.persistManager.loadCluster('local', None)

        baseConf = config.configFromStream(open('/tmp/machine.conf'),
                                           base=config.configFromEnv())
        
        conf = config.configFromMap({'config_loaded': True},
                                    base=baseConf)

        if (cluster.credName == 'local' and
            conf('MASTER_IP') not in [cluster.master['public_dns'],
                                      cluster.master['private_dns']]):
            master = dict(instance_id='local',
                          ami_id=None,
                          public_dns=conf('MASTER_IP'),
                          private_dns=conf('MASTER_IP'),
                          state='running',
                          key=None,
                          index=None,
                          instance_type=None,
                          launch=None,
                          availability_zone=None,
                          monitor=None,
                          spot_request_id=None,
                          bid_price=None)
            cluster = cluster.setMaster(master).update(config=conf)
            yield state.persistManager.saveCluster(cluster)
        
        defer.returnValue(cluster)
    except persist.ClusterNotFoundError:
        credential = _credential()

        credTaskName = yield cred_client.saveCredential(credential['name'],
                                                        credential['desc'],
                                                        credential['ctype'],
                                                        credential['cert'],
                                                        credential['pkey'],
                                                        credential['metadata'],
                                                        credential['conf'])

        ## Wait for credential to be added.
        ## TODO: Should handle failure here
        yield tasks_tx.blockOnTask('localhost',
                                   'local',
                                   credTaskName)

        credClient = cred_client.CredentialClient('local',
                                                  mq,
                                                  state.conf)

        ## If it isn't a local ctype then we need to wait for
        ## the credential to come alive
        if credential['ctype'] != 'local':
            instances = yield credClient.listInstances()
        else:
            instances = []

        baseConf = config.configFromStream(open('/tmp/machine.conf'),
                                           base=config.configFromEnv())
        conf = config.configFromMap({'config_loaded': True},
                                    base=baseConf)
        cluster = persist.Cluster('local',
                                  None,
                                  'local',
                                  conf)

        startTaskName = yield tasks_tx.createTaskAndSave('startCluster', 1)
        yield tasks_tx.updateTask(startTaskName,
                                  lambda t : t.setState(tasks_tx.task.TASK_COMPLETED).progress())
        
        cluster = cluster.update(startTask=startTaskName)

        masterIp = cluster.config('MASTER_IP')
        masterIdx = func.find(lambda i : masterIp in [i['public_dns'], i['private_dns']],
                              instances)

        if masterIdx is not None:
            master = instances[masterIdx]
        else:
            master = dict(instance_id='local',
                          ami_id=None,
                          public_dns=masterIp,
                          private_dns=masterIp,
                          state='running',
                          key=None,
                          index=None,
                          instance_type=None,
                          launch=None,
                          availability_zone=None,
                          monitor=None,
                          spot_request_id=None,
                          bid_price=None)
            
        cluster = cluster.setMaster(master)
        cluster = cluster.setState(cluster.RUNNING)
        yield state.persistManager.saveCluster(cluster)
        defer.returnValue(cluster)


def resumePendingClusters(mq, state):
    pass


@defer.inlineCallbacks
def runSubscribe(mq, state, modules):
    for f in modules:
        yield defer.maybeDeferred(f, mq, state)
        

def subscribeToQueues(mq, state):
    runSubscribe(mq,
                 state,
                 [loadLocalCluster,
                  removeDeadClusters,
                  resumePendingClusters,
                  cluster_mq_startcluster.subscribe,
                  cluster_mq_terminate.subscribe,
                  cluster_mq_terminateinstances.subscribe,
                  cluster_mq_addinstances.subscribe,
                  cluster_mq_list.subscribe,
                  cluster_mq_config.subscribe,
                  clusters_cleanup.subscribe,
                  cluster_refresh.subscribe])
    

def makeService(conf):
    mqService = client.makeService(conf)

    mqFactory = mqService.mqFactory

    # State is currently not used, but kept around for future purposes
    state = State(conf)

    subscribeToQueues(mqFactory, state)

    return mqService

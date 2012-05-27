from twisted.internet import defer

from igs.utils import functional as func

from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.internal_client import credentials as cred_client

from vappio_tx.www_client import clusters as clusters_client_www


@defer_utils.timeIt
@defer.inlineCallbacks
def terminateInstancesByAttribute(persistManager,
                                  credClient,
                                  clusterName,
                                  userName,
                                  byAttribute,
                                  attributeValues):
    
    cluster = yield persistManager.loadCluster(clusterName, userName)

    instances = [i
                 for i in cluster.execNodes + cluster.dataNodes
                 if i[byAttribute] in attributeValues]
    
    yield defer_utils.mapSerial(credClient.terminateInstances,
                                func.chunk(5, instances))

    defer.returnValue(cluster.removeExecNodes(instances).removeDataNodes(instances))

@defer_utils.timeIt
@defer.inlineCallbacks
def _handleTerminateInstances(request):
    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.setState(tasks_tx.task.TASK_RUNNING))

    cluster = request.state.persistManager.loadCluster(request.body['cluster_name'],
                                                       request.body['user_name'])
    credClient = cred_client.CredentialClient(cluster.credName,
                                              request.mq,
                                              request.state.conf)
    if request.body['cluster_name'] != 'local':
        try:
            remoteTaskName = yield clusters_client_www.terminateInstances(
                cluster.master['public_dns'],
                'local',
                request.body['user_name'],
                request.body['by_attribute'],
                request.body['attribute_values'])
            
            localTask = yield tasks_tx.loadTask(request.body['task_name'])
            yield tasks_tx.blockOnTaskAndForward('localhost',
                                                 request.body['cluster_name'],
                                                 remoteTaskName,
                                                 localTask)
        except:
            yield terminateInstancesByAttribute(credClient,
                                                request.body['cluster_name'],
                                                request.body['user_name'],
                                                request.body['by_attribute'],
                                                request.body['attribute_values'])
            
    else:
        yield terminateInstancesByAttribute(credClient,
                                            'local',
                                            None,
                                            request.body['by_attribute'],
                                            request.body['attributes_values'])

    defer.returnValue(request)


@defer.inlineCallbacks
def handleTerminateInstances(request):
    ret = yield request.state.clusterLocks.run((request.body['cluster_name'],
                                                request.body['user_name']),
                                               _handleTerminateInstances,
                                               request)
    defer.returnValue(ret)


def subscribe(mq, state):
    createAndForward = queue.createTaskAndForward(state.conf('clusters.terminateinstances_queue'),
                                                  'terminateInstances',
                                                  1)
    processTerminateInstancesPipe = defer_pipe.pipe([queue.keysInBody(['cluster_name',
                                                                       'user_name',
                                                                       'by_attribute'
                                                                       'attribute_values']),
                                                     createAndForward])
    
    processTerminateInstances = queue.returnResponse(processTerminateInstancesPipe)

    queue.subscribe(mq,
                    state.conf('clusters.terminateinstances_www'),
                    state.conf('clusters.concurrent_terminateinstances'),
                    queue.wrapRequestHandler(state, processTerminateInstances))

    queue.subscribe(mq,
                    state.conf('clusters.terminateinstances_queue'),
                    state.conf('clusters.concurrent_terminateinstances'),
                    queue.wrapRequestHandlerTask(state, handleTerminateInstances))

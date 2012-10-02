import os

from twisted.internet import defer

from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.clusters import instance_flow

from vappio_tx.internal_client import credentials as cred_client

@defer_utils.timeIt
@defer.inlineCallbacks
def _handleAddInstances(request):
    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.setState(tasks_tx.task.TASK_RUNNING))

    cluster = yield request.state.persistManager.loadCluster(request.body['cluster'],
                                                             request.body['user_name'])

    credClient = cred_client.CredentialClient(cluster.credName,
                                              request.mq,
                                              request.state.conf)

    cType = yield credClient.getCType()

    if cType != 'local':
        if request.body['num_exec'] > 0:
            yield instance_flow.startExecs(request.state,
                                           credClient,
                                           request.body['task_name'],
                                           request.body['num_exec'],
                                           request.body.get('exec_instance_type', None),
                                           cluster)
    
    defer.returnValue(request)


def forwardOrCreateTask(url, dstQueue, tType, numTasks):
    return defer_pipe.runPipeCurry(defer_pipe.pipe([queue.forwardRequestToCluster(url),
                                                    queue.createTaskAndForward(dstQueue,
                                                                               tType,
                                                                               numTasks)]))

@defer.inlineCallbacks
def handleAddInstances(request):
    ret = yield request.state.clusterLocks.run((request.body['cluster'],
                                                request.body['user_name']),
                                               _handleAddInstances,
                                               request)
    defer.returnValue(ret)


def subscribe(mq, state):
    url = (state.conf('www.url_prefix') +
           '/' +
           os.path.basename(state.conf('clusters.addinstances_www')))
    forwardOrCreate = forwardOrCreateTask(url,
                                          state.conf('clusters.addinstances_queue'),
                                          'addInstances',
                                          4)

    processAddPipe = defer_pipe.pipe([queue.keysInBody(['cluster',
                                                        'user_name',
                                                        'num_exec',
                                                        'num_data']),
                                      forwardOrCreate])
    
    processAddInstances = queue.returnResponse(processAddPipe)

    queue.subscribe(mq,
                    state.conf('clusters.addinstances_www'),
                    state.conf('clusters.concurrent_addinstances'),
                    queue.wrapRequestHandler(state, processAddInstances))

    queue.subscribe(mq,
                    state.conf('clusters.addinstances_queue'),
                    state.conf('clusters.concurrent_addinstances'),
                    queue.wrapRequestHandlerTask(state, handleAddInstances))

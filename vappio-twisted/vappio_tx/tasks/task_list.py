import os

from twisted.internet import defer

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.tasks import persist

@defer.inlineCallbacks
def handleTaskList(request):
    if 'task_name' in request.body:
        task = yield persist.loadTask(request.body['task_name'])
        request = request.update(response=[persist.taskToDict(task)])
    else:
        tasks = yield persist.loadAllTasks()
        request = request.update(response=[persist.taskToDict(t) for t in tasks])

    defer.returnValue(request)
    
def _forwardToCluster(conf, queueUrl):
    return queue.forwardRequestToCluster(conf('www.url_prefix') + '/' + os.path.basename(queueUrl))
    
def subscribe(mq, state):
    processTaskList = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                              'user_name']),
                                                            _forwardToCluster(state.conf,
                                                                              state.conf('tasks.list_www')),
                                                            handleTaskList]))
    
    queue.subscribe(mq,
                    state.conf('tasks.list_www'),
                    state.conf('tasks.concurrent_list'),
                    queue.wrapRequestHandler(state, processTaskList))
    

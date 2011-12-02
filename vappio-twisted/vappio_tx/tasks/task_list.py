# DANGER WILL ROBINSON!
# Be very weary of adding any caching behavior to this.  For starters,
# it's probably useless, unless some pipelines are getting messages so
# large that loading it from mongo is prohibitively expensive.  Secondly
# and most importantly is that webservices ARE NOT the sole gateway to
# modifying tasks.  People expect to be able to modify tasks by acessing
# the database directly.  That means any caching layer added here is bound
# to fail.
#
# This expected behavior is silly, I know, but it is a balance between this
# silly behavior and a possible security hole where anyone with webservice
# access can modify a task.
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
    

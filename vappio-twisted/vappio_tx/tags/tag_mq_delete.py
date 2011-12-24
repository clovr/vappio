import os

from twisted.internet import defer

from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.tasks import tasks as tasks_tx

@defer_utils.timeIt
@defer.inlineCallbacks
def _handleDeleteTag(request):
    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.setState(tasks_tx.task.TASK_RUNNING).update(numTasks=1))

    yield request.state.tagPersist.removeTag(request.body['tag_name'],
                                             request.body.get('delete_everything', False))

    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.progress())

    defer.returnValue(request)

def _forwardToCluster(conf, queueUrl):
    return queue.forwardRequestToCluster(conf('www.url_prefix') + '/' + os.path.basename(queueUrl))

def handleDeleteTag(request):
    lock = request.state.tagLocks.setdefault(('local', request.body['tag_name']),
                                             defer.DeferredLock())
    return lock.run(_handleDeleteTag, request)


def subscribe(mq, state):
    processDeleteTag = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                               'tag_name']),
                                                             _forwardToCluster(state.conf,
                                                                               state.conf('tags.delete_www')),
                                                             queue.createTaskAndForward(state.conf('tags.delete_queue'),
                                                                                        'deleteTag',
                                                                                        0)]))

    queue.subscribe(mq,
                    state.conf('tags.delete_www'),
                    state.conf('tags.concurrent_delete'),
                    queue.wrapRequestHandler(state, processDeleteTag))

    queue.subscribe(mq,
                    state.conf('tags.delete_queue'),
                    state.conf('tags.concurrent_delete'),
                    queue.wrapRequestHandlerTask(state, handleDeleteTag))

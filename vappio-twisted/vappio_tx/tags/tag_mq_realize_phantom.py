import os

from twisted.python import log

from twisted.internet import defer

from igs.utils import config
from igs.utils import functional as func

from igs_tx.utils import defer_pipe
from igs_tx.utils import commands

from vappio_tx.utils import queue

from vappio_tx.tags import tag_mq_data

from vappio_tx.www_client import clusters as www_clusters

from vappio_tx.tasks import tasks as tasks_tx


class Error(Exception):
    pass

class RunCommandError(Error):
    pass

def _runCommand(_ctype, _baseDir, command, _phantomConfig):
    def _reraise(stderr):
        raise RunCommandError(''.join(stderr))
    stderr = []
    return commands.runProcess(commands.shell(command),
                               stderrf=stderr.append,
                               log=True).addErrback(lambda _ : _reraise(stderr))

def _realizePhantom(ctype, baseDir, phantom):
    phantomConfig = config.configFromMap(func.updateDict(phantom,
                                                         {'ctype': ctype,
                                                          'base_dir': baseDir}),
                                         lazy=True)

    download = str(phantomConfig('cluster.%s.url' % ctype,
                                 default=phantomConfig('cluster.%s.command' % ctype,
                                                       default=phantomConfig('cluster.ALL.command'))))
                   
    if download.startswith('http://'):
        #_downloadHttp(ctype, baseDir, download, phantomConfig)
        pass
    elif download.startswith('s3://'):
        ##
        # We might ened to modify realizePhantom to take a conf that will have our s3 credentails in it
        #_downloadS3(ctype, baseDir, download, phantomConfig)
        pass
    else:
        ##
        # It's a command:
        return _runCommand(ctype, baseDir, download, phantomConfig)

@defer.inlineCallbacks
def handleRealizePhantom(request):
    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.setState(tasks_tx.task.TASK_RUNNING).update(numTasks=1))
    
    localCluster = yield www_clusters.loadCluster('localhost', 'local', request.body['user_name'])
    ctype = localCluster['config']['general.ctype']

    dstTagPath = os.path.join(localCluster['config']['dirs.upload_dir'],
                              request.body['tag_name'])

    metadata = func.updateDict(request.body['metadata'], {'tag_base_dir': dstTagPath})
    
    yield commands.runProcess(['mkdir', '-p', dstTagPath])

    try:
        yield _realizePhantom(ctype, dstTagPath, request.body['phantom'])
    except RunCommandError, err:
        yield tasks_tx.updateTask(request.body['task_name'],
                                  lambda t : t.addMessage(tasks_tx.task.MSG_ERROR, str(err)))
        raise err

    yield tag_mq_data.tagData(request.state,
                              tagName=request.body['tag_name'],
                              taskName=request.body['task_name'],
                              files=[dstTagPath],
                              metadata=metadata,
                              action=tag_mq_data.ACTION_OVERWRITE,
                              recursive=True,
                              expand=True,
                              compressDir=None)

    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.progress())

    defer.returnValue(request)

def _forwardToCluster(conf, queueUrl):
    return queue.forwardRequestToCluster(conf('www.url_prefix') + '/' + os.path.basename(queueUrl))

def subscribe(mq, state):
    processRealizePhantom = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                    'tag_name',
                                                                                    'user_name',
                                                                                    'phantom',
                                                                                    'metadata']),
                                                                  _forwardToCluster(state.conf,
                                                                                    state.conf('tags.realize_www')),
                                                                  queue.createTaskAndForward(state.conf('tags.realize_queue'),
                                                                                             'realizePhantom',
                                                                                             0)]))
    queue.subscribe(mq,
                    state.conf('tags.realize_www'),
                    state.conf('tags.concurrent_realize'),
                    queue.wrapRequestHandler(state, processRealizePhantom))

    queue.subscribe(mq,
                    state.conf('tags.realize_queue'),
                    state.conf('tags.concurrent_realize'),
                    queue.wrapRequestHandlerTask(state, handleRealizePhantom))

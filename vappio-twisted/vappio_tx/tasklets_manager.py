#
# This receives tasklet work to do, creates any task information and then
# fires off the tasklet work in the background and waits for the result
import os
import StringIO

from twisted.internet import defer

from vappio.tasks import task

from igs_tx.utils import commands
from igs_tx.utils import errors
from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.mq import client

from vappio_tx.tasks import tasks

class InvalidMetricNameError(Exception):
    pass

class MetricError(Exception):
    def __init__(self, m, stderr):
        self.m = m
        self.stderr = stderr

    def __str__(self):
        return 'Failed on metric "%s" with error "%s"' % (self.m, self.stderr)

def splitAndSanitizeMetrics(metrics):
    """
    This splits metrics on '|' and puts the path to where the metrics are infront of
    every command and throws an exception if a the command starts with something
    untrustworthy (like a relative path or quotes)

    Right now this does a trivial split on '|', this should be fixed though
    """
    def sanitize(m):
        if m[0] in ['.', '\'', '"', '/'] or '..' in m:
            raise InvalidMetricNameError('Metric cannot start with funny characters: ' + m)

        return os.path.join('/opt', 'vappio-metrics', m.strip())
    
    return [sanitize(m) for m in metrics.split('|')]


def parseCmd(s):
    return s.split(' ')


def runTasklet(taskName, initialText, tasklets):
    def _raise(tasklet, err):
        raise MetricError(tasklet, err)
    
    def _run(text, tasklet):
        stdout = StringIO.StringIO()
        stderr = StringIO.StringIO()

        p = commands.runProcess(parseCmd(tasklet),
                                initialText=text,
                                stdoutf=stdout.write,
                                stderrf=stderr.write)
        p.addCallback(lambda _ : tasks.updateTask(taskName,
                                                  lambda t : t.progress()))
        p.addCallback(lambda _ : stdout.getvalue())
        p.addErrback(lambda _ : _raise(tasklet, stderr.getvalue()))
        return p

    return defer_utils.fold(_run, initialText, tasklets)

@defer.inlineCallbacks
def runTaskletWithTask(taskName, initialText, tasklets):
    yield tasks.updateTask(taskName,
                           lambda t : t.setState(task.TASK_RUNNING
                                                 ).addMessage(task.MSG_SILENT,
                                                              'Starting to run ' + ' | '.join(tasklets)).update(numTasks=len(tasklets)))

    try:
        output = yield runTasklet(taskName, initialText, tasklets)
        yield tasks.updateTask(taskName,
                               lambda t : t.setState(task.TASK_COMPLETED
                                                     ).addMessage(task.MSG_NOTIFICATION, 'Completed'
                                                                  ).addResult(output))
    except MetricError, err:
        yield tasks.updateTask(taskName,
                               lambda t : t.setState(task.TASK_FAILED
                                                     ).addException(str(err), err, errors.getStacktrace()))
        raise err


    
    
def handleRunTasklet(request):
    initialConf = request.body['conf']
    initialText = ('\n'.join(['kv'] + [k + '=' + v for k, v in initialConf.iteritems()]) + '\n').encode('utf_8')
    tasklets = splitAndSanitizeMetrics(request.body['tasklet'].encode('utf_8'))
    return runTaskletWithTask(request.body['task_name'], initialText, tasklets).addCallback(lambda _ : request)
    

def sendTaskname(request):
    queue.returnQueueSuccess(request.mq, request.body['return_queue'], request.body['task_name'])
    return defer_pipe.ret(request)

def forwardOrCreate(url, dstQueue, tType, numTasks):
    return defer_pipe.runPipeCurry(defer_pipe.pipe([queue.forwardRequestToCluster(url),
                                                    queue.createTaskAndForward(dstQueue,
                                                                               tType,
                                                                               numTasks)]))

def makeService(conf):
    mqService = client.makeService(conf)
    mqFactory = mqService.mqFactory


    processRequest = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                             'tasklet',
                                                                             'conf']),
                                                           forwardOrCreate(
                                                               conf('www.url_prefix') + '/' +
                                                               os.path.basename(conf('tasklets.tasklets_www')),
                                                               conf('tasklets.tasklets_queue'),
                                                               'runTasklets',
                                                               1),
                                                           sendTaskname]),
                                          queue.failureMsg)


    queue.subscribe(mqFactory,
                    conf('tasklets.tasklets_www'),
                    conf('tasklets.concurrent_tasklets'),
                    queue.wrapRequestHandler(None, processRequest))


    processRunTasklet = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['tasklet',
                                                                                'conf']),
                                                              handleRunTasklet]),
                                             queue.failureMsg)
    
    queue.subscribe(mqFactory,
                    conf('tasklets.tasklets_queue'),
                    conf('tasklets.concurrent_tasklets'),
                    queue.wrapRequestHandlerTask(None, processRunTasklet))
    
    
    return mqService
    

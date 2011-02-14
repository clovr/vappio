#
# This receives tasklet work to do, creates any task information and then
# fires off the tasklet work in the background and waits for the result
import os
import StringIO
import json

from vappio.tasks import task

from igs.utils import core

from igs_tx.utils import commands
from igs_tx.utils import errors

from vappio_tx.utils import core as vappio_tx_core
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

def runMetrics(taskName, initialText, metrics):
    def _errback(metric, stderr):
        raise MetricError(metric, stderr.getvalue())
    
    def _run(initialText, ms):
        try:
            m = ms.next()
            stdout = StringIO.StringIO()
            stderr = StringIO.StringIO()
            p = commands.runProcess(parseCmd(m),
                                    initialText=initialText.getvalue(),
                                    stdoutf=stdout.write,
                                    stderrf=stderr.write)
            tasks.updateTask(taskName,
                             lambda t : t.progress()).addCallback(lambda _ : p)
            p.addErrback(lambda _ : _errback(m, stderr))
            p.addCallback(lambda _ : _run(stdout, ms))
            return p
        except StopIteration:
            return initialText.getvalue()

    metricsIter = iter(metrics)
    return _run(StringIO.StringIO(initialText), metricsIter)

def runMetricsWithTask(taskName, initialText, metrics):
    d = tasks.updateTask(taskName,
                         lambda t : t.setState(task.TASK_RUNNING
                                               ).addMessage(task.MSG_SILENT,
                                                            'Starting to run ' + ' | '.join(metrics)).update(numTasks=len(metrics)))
    d.addCallback(lambda _ : runMetrics(taskName, initialText, metrics))
    d.addCallback(lambda o : tasks.updateTask(taskName,
                                              lambda t : t.setState(task.TASK_COMPLETED
                                                                    ).addMessage(task.MSG_NOTIFICATION, 'Completed'
                                                                                 ).addResult(o)))
    
    def _err(f):
        tasks.updateTask(taskName,
                         lambda t : t.setState(task.TASK_FAILED
                                               ).addException(f.getErrorMessage(), f, errors.stackTraceToString(f)))

    d.addErrback(_err)

    return d
    
    
def handleMsg(mq, body):
    request = body
    initialConf = request['conf']
    initialText = ('\n'.join(['kv'] + [k + '=' + v for k, v in initialConf.iteritems()]) + '\n').encode('utf_8')
    metrics = splitAndSanitizeMetrics(request['metrics'].encode('utf_8'))
    runMetricsWithTask(request['task_name'], initialText, metrics)
    

def makeService(conf):
    mqService = client.makeService(conf)
    mqFactory = mqService.mqFactory


    queue.ensureRequestAndSubscribeForwardTask(mqFactory,
                                               vappio_tx_core.QueueSubscription(ensureF=core.keysInDictCurry(['conf', 'metrics']),
                                                                                successF=handleMsg,
                                                                                failureF=None),
                                               'runTasklets',
                                               conf('www.url_prefix') + '/' + os.path.basename(conf('tasklets.tasklets_www')),
                                               conf('tasklets.tasklets_www'),
                                               conf('tasklets.tasklets_queue'),
                                               conf('tasklets.concurrent_tasklets'))
        

    
    return mqService
    
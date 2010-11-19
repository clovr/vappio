#
# This receives tasklet work to do, creates any task information and then
# fires off the tasklet work in the background and waits for the result
import os
import StringIO
import json

from twisted.python import log

from igs_tx.utils import commands
from igs_tx.utils import errors

from vappio_tx.mq import client

from vappio_tx.tasks import tasks
from vappio.tasks import task

class InvalidMetricNameError(Exception):
    pass

class MetricError(Exception):
    def __init__(self, m, stderr):
        self.m = m
        self.stderr = stderr

    def __str__(self):
        return 'Failed on metric: ' + self.m

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
    return s.split(' ', 1)[0]

def runMetrics(initialText, metrics):
    def _errback(metric, stderr):
        raise MetricError(metric, stderr)
    
    def _run(initialText, ms):
        try:
            m = ms.next()
            stdout = StringIO.StringIO()
            stderr = StringIO.StringIO()
            p = commands.runProcess(parseCmd(m), initialText=initialText.getvalue(), stdoutf=stdout.write, stderrf=stderr.write)
            p.addCallback(lambda _ : _run(stdout, ms)).addErrback(lambda _ : _errback(m, stderr))
            return p
        except StopIteration:
            return True

    metricsIter = iter(metrics)
    return _run(StringIO.StringIO(initialText), metricsIter)

def createTask(mq, metrics, retQueue):
    def _err(failure):
        log.err(failure)
        mq.send(retQueue, json.dumps({'success': False}))
        return failure

    def _sendMq(taskName):
        mq.send(retQueue, json.dumps({'success': True, 'data': taskName}))
        return taskName
    
    d = tasks.createTaskAndSave('runMetric', 1, 'Running ' + ' | '.join(metrics))
    d.addCallback(_sendMq)
    d.addErrback(_err)

def runMetricsWithTask(taskName, initialText, metrics):
    d = tasks.updateTask(taskName, lambda t : t.setState(task.TASK_RUNNING
                                                         ).addMessage(task.MSG_SILENT,
                                                                      'Starting to run metric'))
    d.addCallback(lambda _ : runMetrics(initialText, metrics))
    d.addCallback(lambda o : tasks.updateTask(taskName, lambda t : t.setState(task.TASK_COMPLETED
                                                                              ).addMessage(task.MSG_NOTIFICATION, 'Completed'
                                                                                           ).addResult(o).progress()))
    
    def _err(f):
        tasks.updateTask(taskName, lambda t : t.setState(task.TASK_FAILED
                                                         ).addException(f.getErrorMessage(), f, errors.stackTraceToString(f)))
    d.addErrback(_err)
    
    
def handleMsg(mq, msg):
    request = json.loads(msg.body)
    payload = request['payload']
    initialConf = payload['conf']
    initialText = '\n'.join(['kv'] + [k + '=' + v for k, v in initialConf.iteritems()]) + '\n'
    metrics = splitAndSanitizeMetrics(payload['metrics'])
    
    createTask(mq, metrics, request['return_queue']).addCallback(runMetricsWithTask, initialText, metrics)
    

def makeService(conf):
    mqService = client.makeService(conf)
    mqService.mqFactory.subscribe(lambda m : handleMsg(mqService.mqFactory, m), conf('tasklets.queue'), {'prefetch': int(conf('tasklets.concurrent_tasklets'))})
    return mqService
    

#!/usr/bin/env python
import os
import json
import subprocess

from igs.utils import cli
from igs.utils import functional as func

from vappio.core.error_handler import runCatchError, mongoFail
from vappio.tasks import task
from vappio.tasks import utils as task_utils

OPTIONS = [
    ('task_name', '', '--task-name', 'Task name', cli.notNone),
    ('config', '', '--conf', 'JSON Encoded configuration', cli.notNone),
    ('metrics', '', '--metrics', 'String representing metrics to run', cli.notNone)
    ]

class InvalidMetricNameError(Exception):
    pass

class MetricError(Exception):
    pass

def splitAndSanitizeMetrics(metrics):
    """
    This splits metrics on '|' and puts the path to where the metrics are infront of
    every command and throws an exception if a the command starts with something
    untrustworthy (like a relative path or quotes)

    Right now this does a trivial split on '|', this should be fixed though
    """
    def sanitize(m):
        if m[0] in ['.', '\'', '"', '/']:
            raise InvalidMetricNameError('Metric cannot start with funny characters: ' + m)

        return os.path.join('/opt', 'vappio-metrics', m.strip())
    
    return [sanitize(m) for m in metrics.split('|')]
    
def runMetrics(conf, metrics):
    """
    Takes a list of metrics to run and runs them one at a time, pushing the output from one
    into the input of another.  They are run one at a time because along the way if one fails the
    next should not be run.
    """
    def run(m, stdin):
        pipe = subprocess.Popen(m, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        stdoutData, stderrData = pipe.communicate(stdin)

        exitCode = pipe.wait()

        # Raise an exception if there was an error
        if exitCode != 0:
            print 'raising?'
            raise MetricError('Metric failed', m, stdoutData, stderrData)

        return stdoutData

    stdin = '\n'.join(['kv'] + [k + '=' + v for k, v in conf.iteritems()]) + '\n'
    for m in metrics:
        stdin = run(m, stdin)

    #
    # Return what the last metric said
    return stdin



def main(options, _args):
    tsk = task.updateTask(task.loadTask(options('general.task_name')
                                        ).setState(task.TASK_RUNNING
                                                   ).addMessage(task.MSG_SILENT, 'Starting to run metric'))

    conf = json.loads(options('general.config'))
    metrics = options('general.metrics')

    metricsSS = splitAndSanitizeMetrics(metrics)

    output = runMetrics(conf, metricsSS)

    task.updateTask(tsk.setState(task.TASK_COMPLETED).addMessage(task.MSG_NOTIFICATION, 'Completed').addResult(output).progress())


if __name__ == '__main__':
    runCatchError(lambda : task_utils.runTaskMain(main,
                                                  *cli.buildConfigN(OPTIONS)),
                  mongoFail(dict(action='runMetrics')))

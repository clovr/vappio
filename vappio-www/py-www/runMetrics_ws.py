#!/usr/bin/env python
import json
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery
from igs.utils.commands import runSystemEx

from vappio.cluster import control as cluster_control

from vappio.tasks.utils import createTaskAndSave


class RunMetrics(CGIPage):
    """
    Metrics requires 3 options:
    name - Name of cluster to run on
    conf - Dictionary of config values
    metrics - A string for what metrics to run.  Metrics are separated by the pipe symbol
    """
    def body(self):
        request = readQuery()

        if request['name'] == 'local':
            taskName = createTaskAndSave('runMetric', 1, 'Running ' + request['metrics'])

            cmd = ['runMetricsR.py',
                   '--task-name=' + taskName,
                   '--conf=\'%s\'' % (json.dumps(request['conf']).encode('string_escape'),),
                   '--metrics=\'%s\'' % (str(request['metrics']).encode('string_escape'),),
                   '>> /tmp/runMetricsR.log 2>&1 &',
                   ]

            runSystemEx(' '.join(cmd))
        else:
            #
            # Forward request on
            cluster = cluster_control.loadCluster(request['name'])
            request['name'] = 'local'
            taskName = performQuery(cluster.master.publicDNS, URL, request)

        return taskName
               

        
generatePage(RunMetrics())

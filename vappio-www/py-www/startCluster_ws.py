#!/usr/bin/env python
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery
from igs.utils.commands import runSystemEx

from vappio.tasks.utils import createTaskAndSave


class StartCluster(CGIPage):
    def body(self):
        request = readQuery()

        ##
        # Starting a cluster requires 2 steps, starting master then starting slaves
        taskName = createTaskAndSave(request['name'] + '-startCluster', 2)
        
        cmd = ['startClusterR.py',
               '--conf=' + request['conf'],
               '--num=' + str(request['num']),
               '--ctype=' + request['ctype'],
               '--name=' + request['name'],
               '--task-name=' + taskName]

        if request['update_dirs']:
            cmd.append('--update_dirs')

        cmd.append('>> /tmp/startCluster.log 2>&1 &')

        runSystemEx(' '.join(cmd))

        return taskName
               

        
generatePage(StartCluster())

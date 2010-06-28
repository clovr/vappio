#!/usr/bin/env python
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery
from igs.utils.commands import runSystemEx

from vappio.tasks.utils import createTaskAndSave

class AddInstances(CGIPage):
    def body(self):
        request = readQuery()

        ##
        # Someone could run multiple addInstances at once, so we will
        # add the time to the end as a cheap trick
        taskName = createTaskAndSave('addInstances', 1)
        
        num = request['num']
        updateDirs = request['update_dirs']

        cmd = ['addInstancesR.py',
               '--num=' + str(num),
               '--task-name=' + taskName]
        
        if updateDirs:
            cmd.append('--update_dirs')

        cmd.append('>> /tmp/addInstances.log 2>&1 &')

        runSystemEx(' '.join(cmd))

        return taskName
               

        
generatePage(AddInstances())

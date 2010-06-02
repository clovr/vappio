#!/usr/bin/env python
##
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery
from igs.utils.errors import TryError

from vappio.webservice.cluster import loadCluster

from vappio.tasks.task import loadTask, loadAllTasks, saveTask, taskToDict

URL = '/vappio/task_ws.py'

class Task(CGIPage):

    def body(self):
        request = readQuery()

        if request['name'] == 'local':
            if 'task_name' in request:
                task = loadTask(request['task_name'])
                return json.dumps([True, [taskToDict(task)]])
            else:
                tasks = loadAllTasks()
                return [taskToDict(t) for t in tasks]
        else:
            ##
            # Forward the request onto the appropriate machine
            cluster = loadCluster('localhost', request['name'])
            request['name'] = 'local'
            return performQuery(cluster.master.publicDNS, URL, request)        
            
        
generatePage(Task())

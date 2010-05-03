#!/usr/bin/env python
##

import json

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQueryNoParse
from igs.utils.errors import TryError

from vappio.webservice.cluster import loadCluster

from vappio.tasks.task import loadTask, saveTask, taskToDict, readMessages

URL = '/vappio/task_ws.py'

class Task(CGIPage):

    def body(self):
        request = readQuery()

        if request['name'] == 'local':
            task = loadTask(request['task_name'])
            if request['read']:
                ##
                # If read is true then we set all of the messages to
                # be read and save that back
                saveTask(readMessages(task))
            return taskToDict(task)
        else:
            ##
            # Forward the request onto the appropriate machine
            cluster = loadCluster('localhost', request['name'])
            request['name'] = 'local'
            return performQueryNoParse(cluster.master.publicDNS, URL, request)        
            
        
generatePage(Task())

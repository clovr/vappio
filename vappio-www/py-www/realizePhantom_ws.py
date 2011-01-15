#!/usr/bin/env python
##
# Uploads a file tag and tags it on remote side
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery
from igs.utils.commands import runSystemEx

from vappio.webservice.cluster import loadCluster

from vappio.tasks.utils import createTaskAndSave

URL = '/vappio/realizePhantom_ws.py'

class RealizePhantom(CGIPage):
    def body(self):
        request = readQuery()

        if request['name'] == 'local':
            taskName = createTaskAndSave('realizeTag', 2, 'Realizing ' + request['tag_name'])

            cmd = ['realizePhantomR.py',
                   '--tag-name=' + request['tag_name'],
                   '--task-name=' + taskName]


            cmd.append('>> /tmp/realizePhantom.log 2>&1 &')

            runSystemEx(' '.join(cmd))

        else:
            ##
            # Forward request on
            cluster = loadCluster('localhost', request['name'])
            request['name'] = 'local'
            taskName = performQuery(cluster['master']['public_dns'], URL, request)

        return taskName
               

        
generatePage(RealizePhantom())


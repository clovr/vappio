#!/usr/bin/env python
##
# Uploads a file tag and tags it on remote side
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery
from igs.utils.commands import runSystemEx

from vappio.cluster.persist_mongo import load

from vappio.tasks.utils import createTaskAndSave

URL = '/vappio/realizePhantom_ws.py'

class RealizePhantom(CGIPage):
    def body(self):
        request = readQuery()

        if request['name'] == 'local':
            taskName = createTaskAndSave(request['tag_name'] + '-realizeTag', 2)

            cmd = ['realizePhantomR.py',
                   '--tag-name=' + request['tag_name'],
                   '--task-name=' + taskName]


            cmd.append('>> /tmp/realizePhantom.log 2>&1 &')

            runSystemEx(' '.join(cmd))

        else:
            ##
            # Forward request on
            cluster = load(request['name'])
            request['name'] = 'local'
            taskName = performQuery(cluster.master.publicDNS, URL, request)

        return taskName
               

        
generatePage(RealizePhantom())


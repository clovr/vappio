#!/usr/bin/env python
##
# Uploads a file tag and tags it on remote side
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery
from igs.utils.commands import runSystemEx

from vappio.tasks.utils import createTaskAndSave

from vappio.webservices.cluster import loadCluster

URL = '/vappio/downloadTag_ws.py'

class DownloadTag(CGIPage):
    def body(self):
        request = readQuery()

        if request['dst_cluster'] == 'local':

            taskName = createTaskAndSave('downloadTag', 2, 'Downloading ' + request['tag_name'])
            
            cmd = ['downloadTagR.py',
                   '--tag-name=' + request['tag_name'],
                   '--task-name=' + taskName,
                   '--src-cluster=' + request['src_cluster'],
                   '--dst-cluster=' + request['dst_cluster']]

            if request['expand']:
                cmd.append('--expand')

            cmd.append('>> /tmp/downloadTag.log 2>&1 &')

            runSystemEx(' '.join(cmd))
        else:
            ##
            # Forward request on
            cluster = loadCluster('localhost', request['dst_cluster'])
            request['dst_cluster'] = 'local'
            taskName = performQuery(cluster.master.publicDNS, URL, request)

        return taskName
               

        
generatePage(DownloadTag())


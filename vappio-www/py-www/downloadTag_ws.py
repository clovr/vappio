#!/usr/bin/env python
##
# Uploads a file tag and tags it on remote side
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery
from igs.utils.commands import runSystemEx
from igs.utils import core

from vappio.tasks.utils import createTaskAndSave

from vappio.webservice.cluster import loadCluster

URL = '/vappio/downloadTag_ws.py'

class DownloadTag(CGIPage):
    def body(self):
        request = readQuery()

        if request['dst_cluster'] == 'local':

            taskName = createTaskAndSave('downloadTag', 2, 'Downloading ' + request['tag_name'])
            
            cmd = ['downloadTagR.py',
                   '--tag-name=' + core.quoteEscape(request['tag_name']),
                   '--task-name=' + core.quoteEscape(taskName),
                   '--src-cluster=' + core.quoteEscape(request['src_cluster']),
                   '--dst-cluster=' + core.quoteEscape(request['dst_cluster'])]

            if request['output_dir']:
                cmd.append('--output-dir=' + core.quoteEscape(request['output_dir']))
                           
            if request['expand']:
                cmd.append('--expand')

            if request['compress']:
                cmd.append('--compress')

            cmd.append('>> /tmp/downloadTag.log 2>&1 &')

            runSystemEx(' '.join(cmd))
        else:
            ##
            # Forward request on
            cluster = loadCluster('localhost', request['dst_cluster'])
            request['dst_cluster'] = 'local'
            taskName = performQuery(cluster['master']['public_dns'], URL, request)

        return taskName
               

        
generatePage(DownloadTag())


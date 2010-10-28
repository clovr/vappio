#!/usr/bin/env python
##
# Uploads a file tag and tags it on remote side
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery
from igs.utils.commands import runSystemEx
from igs.utils import core

from vappio.cluster.control import loadCluster

from vappio.tasks.utils import createTaskAndSave

URL = '/vappio/uploadTag_ws.py'

class UploadTag(CGIPage):
    def body(self):
        request = readQuery()

        if request['src_cluster'] == 'local':

            ##
            # uploading data has 2 steps
            taskName = createTaskAndSave('uploadTag', 2, 'Uploading ' + request['tag_name'])

            
            cmd = ['uploadTagR.py',
                   '--tag-name=' + core.quoteEncode(request['tag_name']),
                   '--task-name=' + core.quoteEncode(taskName),
                   '--src-cluster=' + core.quoteEncode(request['src_cluster']),
                   '--dst-cluster=' + core.quoteEncode(request['dst_cluster'])]

            if request['expand']:
                cmd.append('--expand')

            if request['compress']:
                cmd.append('--compress')

            cmd.append('>> /tmp/uploadTag.log 2>&1 &')

            runSystemEx(' '.join(cmd))

        else:
            ##
            # Forward request on
            cluster = loadCluster(request['src_cluster'])
            request['src_cluster'] = 'local'
            taskName = performQuery(cluster.master.publicDNS, URL, request)

        return taskName
               

        
generatePage(UploadTag())


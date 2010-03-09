#!/usr/bin/env python
##
# Uploads a file tag and tags it on remote side


import json

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery
from igs.utils.commands import runSystemEx

URL = '/vappio/uploadTag_ws.py'

class UploadTag(CGIPage):
    def body(self):
        request = readQuery()

        if request['src_cluster'] == 'local':
            cmd = ['uploadTagR.py',
                   '--tag-name=' + request['tag_name'],
                   '--src-cluster=' + request['src_cluster'],
                   '--dst-cluster=' + request['dst_cluster']]

            if request['expand']:
                cmd.append('--expand')

            cmd.append('>> /tmp/uploadTag.log 2>&1 &')

            runSystemEx(' '.join(cmd))

        else:
            ##
            # Forward request on
            cluster = load(request['src_cluster'])
            request['src_cluster'] = 'local'
            performQuery(cluster.master.publicDNS, URL, request)

        return json.dumps([True, None])
               

        
generatePage(UploadTag())


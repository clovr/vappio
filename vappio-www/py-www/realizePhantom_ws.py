#!/usr/bin/env python
##
# Uploads a file tag and tags it on remote side
import json

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery
from igs.utils.commands import runSystemEx

URL = '/vappio/realizePhantom_ws.py'

class RealizePhantom(CGIPage):
    def body(self):
        request = readQuery()

        if request['name'] == 'local':
            cmd = ['realizePhantomR.py',
                   '--tag-name=' + request['tag_name']]


            cmd.append('>> /tmp/realizePhantom.log 2>&1 &')

            runSystemEx(' '.join(cmd))

        else:
            ##
            # Forward request on
            cluster = load(request['name'])
            request['name'] = 'local'
            performQuery(cluster.master.publicDNS, URL, request)

        return json.dumps([True, None])
               

        
generatePage(RealizePhantom())


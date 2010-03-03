#!/usr/bin/env python
##
# Returns a loaded file tag
import os
import json

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery

from vappio.tags.tagfile import loadTagFile

from vappio.webservice.cluster import loadCluster

URL = '/vappio/queryTag_ws.py'

class QueryTag(CGIPage):

    def body(self):
        request = readQuery()

        if request['name'] == 'local':
            cluster = loadCluster('localhost', 'local')
            
            return json.dumps([True, loadTagFile(os.path.join(cluster.config('dirs.tag_dir'), request['tag_name']))])
        else:
            ##
            # Forward the request onto the appropriate machine
            cluster = loadCluster('localhost', request['name'])
            request['name'] = 'local'
            return performQueryNoParse(cluster.master.publicDNS, URL, request)

generatePage(QueryTag())

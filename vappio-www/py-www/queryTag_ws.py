#!/usr/bin/env python
##
# Returns a loaded file tag
import os
import json

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQueryNoParse
from igs.utils.config import configToDict

from vappio.tags.tagfile import loadTagFile, loadAllTagFiles

from vappio.webservice.cluster import loadCluster

URL = '/vappio/queryTag_ws.py'

class QueryTag(CGIPage):

    def body(self):
        request = readQuery()

        if request['name'] == 'local':
            cluster = loadCluster('localhost', 'local')
            if 'tag_name' in request:
                return json.dumps([True, [configToDict(loadTagFile(os.path.join(cluster.config('dirs.tag_dir'), request['tag_name'])))]])
            else:
                return json.dumps([True, [configToDict(t) for t in loadAllTagFiles(cluster.config('dirs.tag_dir'))]])
        else:
            ##
            # Forward the request onto the appropriate machine
            cluster = loadCluster('localhost', request['name'])
            request['name'] = 'local'
            return performQueryNoParse(cluster.master.publicDNS, URL, request)

generatePage(QueryTag())

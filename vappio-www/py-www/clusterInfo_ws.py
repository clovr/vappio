#!/usr/bin/env python
##
# This script serves double duty.  It can either return local information or proxy out to another cluster

import json

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQueryNoParse

from vappio.cluster.control import clusterToDict
from vappio.cluster.persist_mongo import load



URL = '/vappio/clusterInfo_ws.py'

class ClusterInfo(CGIPage):

    def body(self):
        request = readQuery()
        if request['name'] == 'local':
            cluster = load('local')
            return json.dumps([True, clusterToDict(cluster)])
        else:
            ##
            # Forward the request onto the appropriate machine
            cluster = load(request['name'])
            request['name'] = 'local'
            return performQueryNoParse(cluster.master.publicDNS, URL, request)
                           
        
        
generatePage(ClusterInfo())

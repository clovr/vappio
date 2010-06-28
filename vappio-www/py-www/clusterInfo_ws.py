#!/usr/bin/env python
##
# This script serves double duty.  It can either return local information or proxy out to another cluster
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery
from igs.utils.errors import TryError

from vappio.cluster.control import clusterToDict
from vappio.cluster.persist_mongo import load



URL = '/vappio/clusterInfo_ws.py'

class ClusterInfo(CGIPage):

    def body(self):
        ##
        # If reading the query fails just get the
        # information on the local cluster
        try:
            request = readQuery()
        except:
            request = dict(name='local')


        ##
        # If partial is set it means it's okay to return whatever
        # TryError gave back
        try:
            cluster = load(request['name'])
            return clusterToDict(cluster)
        except TryError, err:
            if request['partial']:
                cluster = err.result
                return clusterToDict(cluster)
            else:
                raise
            
        
generatePage(ClusterInfo())

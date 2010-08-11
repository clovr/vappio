#!/usr/bin/env python
##
# This script serves double duty.  It can either return local information or proxy out to another cluster
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery
from igs.utils.errors import TryError

from vappio.cluster import control as cluster_ctl
from vappio.cluster.persist_mongo import ClusterLoadIncompleteError



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
            cluster = cluster_ctl.loadCluster(request['name'])
            return cluster_ctl.clusterToDict(cluster)
        except ClusterLoadIncompleteError, err:
            if request['partial']:
                return cluster_ctl.clusterToDict(err.cluster)
            else:
                raise
            
        
generatePage(ClusterInfo())

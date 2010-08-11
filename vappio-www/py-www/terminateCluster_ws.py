#!/usr/bin/env python
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery

from vappio.cluster import control as cluster_ctl
from vappio.cluster import persist_mongo

URL = '/vappio/terminateCluster_ws.py'

class TerminateCluster(CGIPage):

    def body(self):
        request = readQuery()

        ##
        # If 'force' is set to true, it means if we will allow loadCluster to give back
        # as much info as it can if its attempt to load cluster info fails such as
        # a remote machine being down
        try:
            cluster = cluster_ctl.loadCluster(request['name'])
        except persist_mongo.ClusterLoadIncompleteError, err:
            if request['force']:
                cluster = err.cluster
            else:
                raise
        cluster.terminate()
        cluster_ctl.removeCluster(request['name'])
        return None

generatePage(TerminateCluster())

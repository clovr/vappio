#!/usr/bin/env python
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQueryNoParse
from igs.utils.config import configToDict
from igs.utils.errors import TryError

from vappio.cluster.control import terminateCluster
from vappio.webservice.cluster import loadCluster
from vappio.cluster.persist_mongo import cleanUp

URL = '/vappio/terminateCluster_ws.py'

class TerminateCluster(CGIPage):

    def body(self):
        request = readQuery()

        ##
        # If 'force' is set to true, it means if we will allow loadCluster to give back
        # as much info as it can if its attempt to load cluster info fails such as
        # a remote machine being down
        cluster = loadCluster('localhost', request['name'], request['force'])
        terminateCluster(cluster)
        cleanUp(request['name'])
        return None

generatePage(TerminateCluster())

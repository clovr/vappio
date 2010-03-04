#!/usr/bin/env python

import json

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQueryNoParse
from igs.utils.config import configToDict

from vappio.cluster.control import terminateCluster
from vappio.webservice.cluster import loadCluster

URL = '/vappio/terminateCluster_ws.py'

class TerminateCluster(CGIPage):

    def body(self):
        request = readQuery()

        cluster = loadCluster('localhost', request['name'])
        terminateCluster(cluster)
        return json.dumps([True, True])

generatePage(TerminateCluster())

#!/usr/bin/env python
##
import json

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery

from vappio.cluster.persist_mongo import listClusters

class ListClusters(CGIPage):
    def body(self):

        return json.dumps([True, listClusters()])
               

        
generatePage(ListClusters())


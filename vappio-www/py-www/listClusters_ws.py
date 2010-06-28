#!/usr/bin/env python
##
from igs.cgi.handler import CGIPage, generatePage

from vappio.cluster.persist_mongo import listClusters

class ListClusters(CGIPage):
    def body(self):
        return listClusters()
               

        
generatePage(ListClusters())


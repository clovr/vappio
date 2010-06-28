#!/usr/bin/env python
##
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery

from vappio.credentials import manager

from vappio.webservices.cluster import loadCluster

URL = '/vappio/credential_ws.py'

class Credential(CGIPage):

    def body(self):
        request = readQuery()

        if request['name'] == 'local':
            if 'cred' in request:
                manager.saveCredential(manager.credentialFromDict(request['cred']))
                return None
            else:
                publicCreds = [manager.publicCredentialToDict(manager.credentialToPublicCredential(c))
                               for c in manager.loadAllCredentials()]
                return publicCreds
        else:
            ##
            # Forward the request onto the appropriate machine
            cluster = loadCluster('localhost', request['name'])
            request['name'] = 'local'
            return performQuery(cluster.master.publicDNS, URL, request)        
            
        
generatePage(Credential())

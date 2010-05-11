#!/usr/bin/env python
##

import json

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQueryNoParse
from igs.utils.errors import TryError

from vappio.credentials import manager

URL = '/vappio/credential_ws.py'

class Credential(CGIPage):

    def body(self):
        request = readQuery()

        if request['name'] == 'local':
            if 'cred' in request:
                manager.saveCredential(manager.credentialFromDict(request['cred']))
                return json.dumps([True, None])
            else:
                publicCreds = [manager.publicCredentialToDict(manager.credentialToPublicCredential(c))
                               for c in manager.loadAllCredentials()]
                return json.dumps([True, publicCreds])
        else:
            ##
            # Forward the request onto the appropriate machine
            cluster = loadCluster('localhost', request['name'])
            request['name'] = 'local'
            return performQueryNoParse(cluster.master.publicDNS, URL, request)        
            
        
generatePage(Credential())

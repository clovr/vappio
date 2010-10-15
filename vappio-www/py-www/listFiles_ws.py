#!/usr/bin/env python
##
import os

from igs.cgi import handler
from igs.cgi import request as cgi_request

from vappio.webservice import cluster as cluster_ws

URL = '/vappio/listFiles_ws.py'

#
# This is a list of base directories that are valid for
# users of this webservice to see
VALID_PATHS = ['/mnt/']

def pathValid(path):

    # Every path in VALID_PATHS ends with a / if it is a dir, so we want to add it
    # if the input path is a directory
    if os.path.isdir(path):
        path += '/'
    for v in VALID_PATHS:
        if path.startswith(v):
            return True

    return False

def getFType(path):
    if os.path.isdir(path):
        return 'dir'
    else:
        return 'file'

class ListFiles(handler.CGIPage):
    def body(self):
        request = cgi_request.readQuery()

        if request['name'] == 'local':
            path = os.path.abspath(request['path'])
            if not pathValid(path):
                raise Exception('The path you provided is invalid')

            return dict([(f,
                          dict(ftype=getFType(os.path.join(path, f)),
                               name=f))
                         for f in os.listdir(path)])
        else:
            #
            # Forward the request onto the appropriate machine
            cluster = cluster_ws.loadCluster('localhost', request['name'])
            request['name'] = 'local'
            return cgi_request.performQuery(cluster.master.publicDNS, URL, request)
                              
handler.generatePage(ListFiles())


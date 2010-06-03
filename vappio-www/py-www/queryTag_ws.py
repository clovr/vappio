#!/usr/bin/env python
##
# Returns a loaded file tag
import os

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery
from igs.utils.config import configToDict
from igs.utils import functional as func


from vappio.tags.tagfile import loadTagFile, loadAllTagFiles

from vappio.webservice.cluster import loadCluster

URL = '/vappio/queryTag_ws.py'

class QueryTag(CGIPage):

    def body(self):
        request = readQuery()

        if request['name'] == 'local':
            cluster = loadCluster('localhost', 'local')
            if 'tag_name' in request:
                return [func.updateDict(configToDict(loadTagFile(os.path.join(cluster.config('dirs.tag_dir'),
                                                                              request['tag_name']))),
                                        dict(name=request['tag_name']))]
            else:
                return [func.updateDict(configToDict(v), dict(name=k))
                        for k, v in
                        loadAllTagFiles(cluster.config('dirs.tag_dir')).iteritems()]
        else:
            ##
            # Forward the request onto the appropriate machine
            cluster = loadCluster('localhost', request['name'])
            request['name'] = 'local'
            return performQuery(cluster.master.publicDNS, URL, request)

generatePage(QueryTag())

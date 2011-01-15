#!/usr/bin/env python
##
# Tags data.
import json

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery
from igs.utils.commands import runSystemEx
from igs.utils import core

from vappio.webservice.cluster import loadCluster

from vappio.tasks.utils import createTaskAndSave


URL = '/vappio/tagData_ws.py'


class TagData(CGIPage):
    def body(self):
        request = readQuery()

        if request['name'] == 'local':

            ##
            # Tagging data only has one step
            taskName = createTaskAndSave('tagData', 1, 'Tagging ' + request['tag_name'])
            
            cmd = ['tagDataR.py',
                   '--tag-name=' + core.quoteEscape(request['tag_name']),
                   '--task-name=' + core.quoteEscape(taskName)]

            if request['tag_base_dir']:
                cmd.append('--tag-base-dir=' + core.quoteEscape(request['tag_base_dir']))
                           
            for i in ['recursive', 'expand', 'append', 'overwrite']:
                if request[i]:
                    cmd.append('--' + i)

            if request['compress']:
                cmd.append('--compress=' + core.quoteEscape(request['compress']))
                
            if request['tag_metadata']:
                cmd.append('--metadata=' + core.quoteEscape(json.dumps(request['tag_metadata'])))
                
            cmd.extend([core.quoteEscape(f) for f in request['files']])

            cmd.append('>> /tmp/tagData.log 2>&1 &')

            runSystemEx(' '.join(cmd))

        else:
            ##
            # Forward request on
            cluster = loadCluster('localhost', request['name'])
            request['name'] = 'local'
            taskName = performQuery(cluster['master']['public_dns'], URL, request)

        return taskName
               

        
generatePage(TagData())

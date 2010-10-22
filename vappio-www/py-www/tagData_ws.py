#!/usr/bin/env python
##
# Tags data.
import json

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery
from igs.utils.commands import runSystemEx

from vappio.cluster.control import loadCluster

from vappio.tasks.utils import createTaskAndSave

URL = '/vappio/tagData_ws.py'

def quoteEncode(s):
    return "'%s'" % str(s).encode('string_escape')

class TagData(CGIPage):
    def body(self):
        request = readQuery()

        if request['name'] == 'local':

            ##
            # Tagging data only has one step
            taskName = createTaskAndSave('tagData', 1, 'Tagging ' + request['tag_name'])
            
            cmd = ['tagDataR.py',
                   '--tag-name=' + quoteEncode(request['tag_name']),
                   '--task-name=' + taskName]

            if request['tag_base_dir']:
                cmd.append('--tag-base-dir=' + quoteEncode(request['tag_base_dir']))
                           
            for i in ['recursive', 'expand', 'append', 'overwrite']:
                if request[i]:
                    cmd.append('--' + i)

            if request['compress']:
                cmd.append('--compress=' + request['compress'])
                
            if request['tag_metadata']:
                cmd.append('--metadata=' + quoteEncode(json.dumps(request['tag_metadata'])))
                
            cmd.extend([quoteEncode(f) for f in request['files']])

            cmd.append('>> /tmp/tagData.log 2>&1 &')

            runSystemEx(' '.join(cmd))

        else:
            ##
            # Forward request on
            cluster = loadCluster(request['name'])
            request['name'] = 'local'
            taskName = performQuery(cluster.master.publicDNS, URL, request)

        return taskName
               

        
generatePage(TagData())

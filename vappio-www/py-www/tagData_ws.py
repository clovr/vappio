#!/usr/bin/env python
##
# Tags data.
import json

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery
from igs.utils.commands import runSystemEx

from vappio.cluster.persist_mongo import load

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
                   '--tag-name=' + request['tag_name'],
                   '--task-name=' + taskName]

            if request['tag_base_dir']:
                cmd.append('--tag-base-dir=' + request['tag_base_dir'])
                           
            for i in ['recursive', 'expand', 'append', 'overwrite']:
                if request[i]:
                    cmd.append('--' + i)

            if request['tag_metadata']:
                cmd.append("--metadata='%s'" % (json.dumps(request['tag_metadata']).encode('string_escape'),))
                
            cmd.extend(request['files'])

            cmd.append('>> /tmp/tagData.log 2>&1 &')

            runSystemEx(' '.join(cmd))

        else:
            ##
            # Forward request on
            cluster = load(request['name'])
            request['name'] = 'local'
            taskName = performQuery(cluster.master.publicDNS, URL, request)

        return taskName
               

        
generatePage(TagData())

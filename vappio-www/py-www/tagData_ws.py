#!/usr/bin/env python
##
# Tags data.
#
# tag-name - What to name the tag
# files - List of files to tag
# recursive - If a file is a directory, recursively its contents to the file list
# expand - If file is an archive of some sort (.bz2, .tar.gz, .tgz) expand it and add the contents to tag
# append - Append the files to the current file list (this will not result in duplicate files in the file list)
#          in other words, if you tag the same file twice with append it will only show up once in the file list
# overwrite - Overwrite the tag with these new contents
#
# Right now, all data is stored in /mnt/staging/data and al ltags in /mnt/staging/tags.  In the future this will likely
# change as we may not want all data in staging because it gets synched out to every node.

import json

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery, performQuery
from igs.utils.commands import runSystemEx

from vappio.cluster.persist_mongo import load

URL = '/vappio/tagData_ws.py'

class TagData(CGIPage):
    def body(self):
        request = readQuery()

        if request['name'] == 'local':
            cmd = ['tagDataR.py', '--tag-name=' + request['tag_name']]

            for i in ['recursive', 'expand', 'append', 'overwrite']:
                if request[i]:
                    cmd.append('--' + i)

            cmd.extend(request['files'])

            cmd.append('>> /tmp/tagData.log 2>&1 &')

            runSystemEx(' '.join(cmd))

        else:
            ##
            # Forward request on
            cluster = load(request['name'])
            request['name'] = 'local'
            performQuery(cluster.master.publicDNS, URL, request)

        return json.dumps([True, None])
               

        
generatePage(TagData())

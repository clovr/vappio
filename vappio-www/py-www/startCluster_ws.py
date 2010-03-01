#!/usr/bin/env python
import os
import cgi
import json

from igs.utils.core import getStrBetween
from igs.utils.config import configFromEnv
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery
from igs.utils.commands import runSystemEx


class StartCluster(CGIPage):
    def body(self):
        conf = configFromEnv()
        request = readQuery()

        cmd = ['startClusterR.py',
               '--conf=' + request['conf'],
               '--num=' + str(request['num']),
               '--ctype=' + request['ctype'],
               '--name=' + request['name']]

        if request['update_dirs']:
            cmd.append('--update_dirs')

        cmd.append('> /tmp/startCluster.log 2>&1 &')

        runSystemEx(' '.join(cmd))

        return json.dumps([True, None])
               

        
generatePage(StartCluster())

#!/usr/bin/env python
import os
import cgi
import json

from igs.utils.core import getStrBetween
from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery
from igs.utils.commands import runSystemEx


class AddInstances(CGIPage):
    def body(self):
        request = readQuery()

        num = request['num']
        updateDirs = request['update_dirs']

        cmd = ['addInstancesR.py', '--num=' + str(num)]
        if updateDirs:
            cmd.append('--update_dirs')

        cmd.append('>> /tmp/addInstances.log 2>&1 &')

        runSystemEx(' '.join(cmd))

        return json.dumps([True, None])
               

        
generatePage(AddInstances())

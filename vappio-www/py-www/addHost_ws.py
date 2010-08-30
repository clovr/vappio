#!/usr/bin/env python
##
import os
import re
import StringIO
import cgi

from igs.cgi.handler import CGIPage, generatePage

from igs.utils import commands


SGE_ROOTBIN = '/var/lib/gridengine/bin/lx26-ia64'


class AddHost(CGIPage):
    def body(self):
        form = cgi.FieldStorage()
        host = form['host'].value
        sio = StringIO.StringIO()
        sgeRootBin = os.path.join(SGE_ROOTBIN)

        if 'ipaddr' in form and re.match('^\d+\.\d+\.\d+\.\d+$', form['ipaddr'].value):
            commands.runSystemEx('addEtcHosts.py %s %s' % (host, form['ipaddr'].value))

        cmd = [os.path.join(sgeRootBin, 'qconf'),
               '-ah',
               host,
               '&>',
               '/tmp/add_host.out']
        
        commands.runSystemEx(' '.join(cmd))
                                

        
generatePage(AddHost())


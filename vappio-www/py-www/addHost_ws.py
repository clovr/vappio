#!/usr/bin/env python
##
import os
import re
import StringIO
import cgi

from igs.cgi.handler import CGIPage, generatePage

from igs.utils import commands


SGE_ROOT = '/opt/sge'


class AddHost(CGIPage):
    def body(self):
        form = cgi.FieldStorage()
        host = form['host'].value
        sio = StringIO.StringIO()
        commands.runSingleProgramEx(os.path.join(SGE_ROOT, 'util', 'arch'), stdoutf=sio.write, stderrf=None)
        arch = sio.getvalue().strip()
        sgeRootBin = os.path.join('/opt', 'sge', 'bin', arch)

        if 'ipaddr' in form and re.match('^\d+\.\d+\.\d+\.\d+$', form['ipaddr'].value):
            commands.runSystemEx('addEtcHosts.py %s %s' % (host, form['ipaddr'].value))

        cmd = [os.path.join(sgeRootBin, 'qconf'),
               '-ah',
               host,
               '&>',
               '/tmp/add_host.out']
        
        commands.runSystemEx(' '.join(cmd))
                                

        
generatePage(AddHost())


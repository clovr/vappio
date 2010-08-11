#!/usr/bin/env python
##
import os
import cgi

from igs.cgi.handler import CGIPage, generatePage

class Announce(CGIPage):
    def body(self):
        form = cgi.FieldStorage()
        open(os.path.join('/mnt',
                          'clovr',
                          'runtime',
                          os.getenv('REMOTE_ADDR') + '-vappio.announce'),
             'a').write(form['msg'].value + '\n')

        
generatePage(Announce())


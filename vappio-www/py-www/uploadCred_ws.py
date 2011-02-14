#!/usr/bin/env python
##
import os
import cgi

from igs.cgi import handler

class UploadCred(handler.CGIPage):
    def body(self):
        form = cgi.FieldStorage()
        

        fname = form['file'].filename
        fin = form['file'].file

        fout = open(os.path.join('/mnt', 'keys', fname), 'w')
        data = fin.read(1024)
        while data:
            fout.write(data)
            data = fin.read(1024)

        return True
        
                              
handler.generatePage(UploadCred())


#!/usr/bin/env python
##
import os
import cgi

from igs.cgi import handler

class UploadFile(handler.CGIPage):
    def body(self):
        form = cgi.FieldStorage()
        

        fname = form['file'].filename
        fin = form['file'].file
        foutname = os.path.join('/mnt', 'user_data', fname)
        fout = open(foutname, 'w')
        data = fin.read(1024)
        while data:
            fout.write(data)
            data = fin.read(1024)

        return foutname
        
                              
handler.generatePage(UploadFile())


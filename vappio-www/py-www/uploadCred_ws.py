#!/usr/bin/env python
##
import os
import cgi
import hashlib

from igs.cgi import handler

class UploadCred(handler.CGIPage):
    def body(self):
        form = cgi.FieldStorage()

        fname = form['file'].filename
        fin = form['file'].file

        md5 = hashlib.md5()
        
        data = fin.read(1024)
        fdata = ''
        while data:
            fdata += data
            md5.update(data)
            data = fin.read(1024)
        
        foutname = os.path.join('/mnt', 'keys', md5.hexdigest())

        fout = open(foutname, 'w')
        fout.write(fdata)
        fout.close()

        return foutname
        
                              
handler.generatePage(UploadCred())


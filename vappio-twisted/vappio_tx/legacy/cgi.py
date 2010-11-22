import os

from twisted.web import twcgi

def addCGIDir(resource, path, filterF=None):
    files = [f for f in os.listdir(path) if filterF and filterF(f)]
    for f in files:
        resource.putChild(f, twcgi.CGIScript(os.path.join(path, f)))

    return files
        

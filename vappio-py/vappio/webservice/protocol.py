from igs.utils import functional as func

from igs.cgi.request import performQuery

DESCRIBEPROTOCOLS_URL = '/vappio/listProtocols_ws.py'

def describeProtocols(host, name):
    return [func.Record(name=p['name'], config=p['config']) for p in performQuery(host, DESCRIBEPROTOCOLS_URL, dict(name=name)) if p['config']]



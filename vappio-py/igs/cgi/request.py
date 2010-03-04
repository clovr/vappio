##
# Functions for creating and reading a request
import cgi
import json
import urllib
import httplib


from igs.utils.errors import TryError

def performQueryNoParse(host, url, var):
    params = urllib.urlencode({'request': json.dumps(var)})
    conn = httplib.HTTPConnection(host, timeout=5)
    conn.request('POST', url, params)
    data = conn.getresponse().read()
    return data

def performQuery(host, url, var):
    """
    params is a dict on of values to pass to server
    """
    data = performQueryNoParse(host, url, var)
    try:
        ok, result = json.loads(data)
        if not ok:
            raise TryError(str(res), None)
        return result
    except:
        raise ValueError('Unknown data: ' + data)

def readQuery():
    form = cgi.FieldStorage()
    return json.loads(form['request'].value)
    

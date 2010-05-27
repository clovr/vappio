##
# Functions for creating and reading a request
import cgi
import json
import urllib
import httplib


from igs.utils.errors import TryError

def performQueryNoParse(host, url, var, timeout=30, debug=False):
    params = urllib.urlencode({'request': json.dumps(var)})
    conn = httplib.HTTPConnection(host, timeout=timeout)
    if debug:
        conn.set_debuglevel(3)
    conn.request('POST', url, params)
    data = conn.getresponse().read()
    return data

def performQuery(host, url, var, timeout=30, debug=False):
    """
    params is a dict on of values to pass to server
    """
    data = performQueryNoParse(host, url, var, timeout=timeout, debug=debug)
    try:
        ok, result = json.loads(data)
        if not ok:
            raise TryError(str(result), None)
        return result
    except TryError:
        raise
    except Exception, err:
        raise ValueError('Unknown data: ' + str(data))

def readQuery():
    form = cgi.FieldStorage()
    return json.loads(form['request'].value)
    

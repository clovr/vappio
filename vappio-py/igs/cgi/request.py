##
# Functions for creating and reading a request
import cgi
import json
import urllib
import httplib
import socket

from igs.utils.errors import TryError

def performQueryNoParse(host, url, var, timeout=30, debug=False):
    def _performQuery():
        params = urllib.urlencode({'request': json.dumps(var)})
        conn = httplib.HTTPConnection(host, timeout=timeout)
        if debug:
            conn.set_debuglevel(3)
        conn.request('POST', url, params)
        return conn.getresponse().read()

    count = 10
    while count > 0:
        try:
            return _performQuery()
        except socket.timeout:
            count -= 1
    

def performQuery(host, url, var, timeout=30, debug=False):
    """
    params is a dict on of values to pass to server
    """
    data = performQueryNoParse(host, url, var, timeout=timeout, debug=debug)
    try:
        ok, result = json.loads(data)
        if not ok:
            raise TryError('Query failed: ' + result['msg'], result)
        return result
    except TryError:
        raise
    except Exception:
        raise ValueError('Unknown data: ' + str(data))

def readQuery():
    form = cgi.FieldStorage()
    return json.loads(form['request'].value)
    

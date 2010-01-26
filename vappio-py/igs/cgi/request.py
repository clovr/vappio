##
# Functions for creating and reading a request
import cgi
import json
import urllib
import httplib

def performQuery(host, url, params):
    """
    params is a dict on of values to pass to server
    """
    params = urllib.urlencode({'request': json.dumps(params)})
    conn = httplib.HTTPConnection(host)
    conn.request('POST', url, params)
    return json.loads(conn.getresponse().read())

def readQuery():
    form = cgi.FieldStorage()
    return json.loads(form['request'].value)

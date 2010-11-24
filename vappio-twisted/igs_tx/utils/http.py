import urllib
import json

from twisted.python import log
from twisted.internet import reactor
from twisted.web import client

from igs.utils import functional as func
from igs.utils import errors

class Timeout(Exception):
    pass

class RetriesFailed(Exception):
    pass

def performQueryNoParse(host, url, var, headers=None, timeout=30, tries=4, debug=False):
    if tries == 0:
        raise RetriesFailed()

    if headers is None:
        headers = {}
    
    d = client.getPage(('http://' + host + url).encode('utf_8'),
                       method='POST',
                       postdata=urllib.urlencode({'request': json.dumps(var)}),
                       headers=func.updateDict(headers, {'Content-Type': 'application/x-www-form-urlencoded'}),
                       timeout=timeout)

    def _error(f):
        log.err(f)
        return performQueryNoParse(host, url, var, headers, timeout, tries - 1, debug)
    d.addErrback(_error)
    return d


def performQuery(host, url, var, headers=None, timeout=30, tries=4, debug=False):
    d = performQueryNoParse(host, url, var, headers, timeout, tries, debug)

    def _parse(rawData):
        result = json.loads(rawData)
        data = result['data']
        if not result['success']:
            raise errors.TryError('Query failed: ' + data['msg'])

        return data

    d.addCallback(_parse)
    return d

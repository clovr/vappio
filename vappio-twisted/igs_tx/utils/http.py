import urllib
import json

from twisted.python import log
from twisted.internet import reactor
from twisted.web import client

from igs.utils import functional as func
from igs.utils import errors

from igs_tx.utils import defer_utils

class Timeout(Exception):
    pass

class RetriesFailed(Exception):
    pass


def _makeGetterFactory(url, factoryFactory, contextFactory=None, connectionTimeout=30,
                       *args, **kwargs):
    """
    This is a rip out of the same function from twisted, I simply needed
    it to support connection timeouts
    """
    scheme, host, port, path = client._parse(url)
    factory = factoryFactory(url, *args, **kwargs)
    if scheme == 'https':
        from twisted.internet import ssl
        if contextFactory is None:
            contextFactory = ssl.ClientContextFactory()
        reactor.connectSSL(host, port, factory, contextFactory, timeout=connectionTimeout)
    else:
        reactor.connectTCP(host, port, factory, timeout=connectionTimeout)
    return factory


def getPage(url, contextFactory=None, connectionTimeout=30, *args, **kwargs):
    """
    Ripping this out of the Twisted code so I can modify it
    to support connection timeouts
    """
    return _makeGetterFactory(
        url,
        client.HTTPClientFactory,
        contextFactory=contextFactory,
        connectionTimeout=connectionTimeout,
        *args, **kwargs).deferred



def performQueryNoParse(host, url, var, headers=None, timeout=30, tries=4, debug=False):
    if tries == 0:
        raise RetriesFailed()

    if headers is None:
        headers = {}
    
    d = defer_utils.tryUntil(tries,
                             lambda : getPage(('http://' + host + url).encode('utf_8'),
                                              method='POST',
                                              postdata=urllib.urlencode({'request': json.dumps(var)}),
                                              headers=func.updateDict(headers, {'Content-Type': 'application/x-www-form-urlencoded'}),
                                              connectionTimeout=timeout,
                                              timeout=timeout),
                             onFailure=defer_utils.sleep(10))

    def _error(f):
        log.err(f)
        return f
    
    d.addErrback(_error)
    return d


def performQuery(host, url, var, headers=None, timeout=30, tries=4, debug=False):
    d = performQueryNoParse(host, url, var, headers, timeout, tries, debug)

    def _parse(rawData):
        result = json.loads(rawData)
        data = result['data']
        if not result['success']:
            log.err(repr(data))
            raise errors.TryError('Query failed: ' + data['msg'], data)

        return data

    d.addCallback(_parse)
    return d

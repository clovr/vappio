import time

from twisted.python import log

# Useful scheduling functions are here, such as .callLater
from twisted.internet import reactor

# Deferred and helper functions defined here
from twisted.internet import defer

# A handy wrapper for http requests.
# .getPage is the raw way to get a page, .performQuery is specific to
# querying vappio webservices
from igs_tx.utils import http

# I have created some utilites to make working with deferreds easier
from igs_tx.utils import defer_utils

# A defer work queue is an queue that allows N deferreds to be run
# concurrently
from igs_tx.utils import defer_work_queue

URLS = ['http://www.igs.umaryland.edu',
        'http://www.reddit.com',
        'http://erlang.org',
        'http://www.gnu.org',
        'http://linux.org',
        'http://clovr.org']


# Each one of these functions will return a deferred that
# will result in a dictionary mapping the URL to the contents

def downloadDeferredSerial(urls):
    """
    Uses deferreds to download the urls in serial
    """
    ret = dict([(url, None)
                for url in urls])

    d = defer.Deferred()

    if urls:
        def _downloadUrl(urlIter):
            try:
                url = urlIter.next()
                downloadDeferred = http.getPage(url,
                                                connectionTimeout=30,
                                                timeout=30)

                def _downloaded(contents):
                    ret[url] = contents
                    reactor.callLater(0.0, _downloadUrl, urlIter)

                downloadDeferred.addCallback(_downloaded)

                def _error(f):
                    # Something went wrong, fail
                    d.errback(f)

                downloadDeferred.addErrback(_error)
                    
            except StopIteration:
                d.callback(ret)

        reactor.callLater(0.0, _downloadUrl, iter(urls))
                                   
    else:
        # If there are no urls to download, just fire our
        # deferred with the empty dict
        d.callback(ret)
        

    return d


def downloadDeferredParallel(urls):
    """
    Uses deferreds to download all the urls in parallel
    """
    def _download(url):
        return http.getPage(url,
                            connectionTimeout=30,
                            timeout=30
                            ).addCallback(lambda content : (url, content))
    
    d = defer.DeferredList([_download(url)
                            for url in urls])

    def _buildReturn(contents):
        ret = {}
        for success, data in contents:
            # If one failed, return the failure
            if success:
                ret[data[0]] = data[1]
            else:
                return data

        return ret

    d.addCallback(_buildReturn)
    return d


def downloadMapSerial(urls):
    """
    Uses mapSerial to download all urls in serial
    """
    getPage = lambda url : http.getPage(url,
                                        connectionTimeout=30,
                                        timeout=30
                                        ).addCallback(lambda content : (url, content))

    d = defer_utils.mapSerial(getPage, urls)
    d.addCallback(dict)
    return d


def downloadDeferWorkQueue(urls):
    """
    Uses a DeferWorkQueue to download URLs with
    dynamic number of concurrent downloads, here we
    will download 10 concurrently.

    NOTE: In this case we aren't handling failures like in the others
    """
    ret = {}

    def _setUrl(url, content):
        ret[url] = content
    
    getPage = lambda url : http.getPage(url,
                                        connectionTimeout=30,
                                        timeout=30
                                        ).addCallback(lambda content : _setUrl(url, content))

    
    dwq = defer_work_queue.DeferWorkQueue(10)

    for url in urls:
        dwq.add(getPage, url)

    return defer_work_queue.waitForCompletion(dwq).addCallback(lambda _ : ret)


@defer.inlineCallbacks
def downloadDeferredSerialInline(urls):
    """
    Uses inline callbacks to download urls in serial.

    Sequential looking code, FTW
    """
    ret = {}
    for url in urls:
        content = yield http.getPage(url,
                                     connectionTimeout=30,
                                     timeout=30)
        ret[url] = content

    defer.returnValue(ret)
    


def _printResults(results):
    print 'Num results:', len(results)
    for url, content in results.iteritems():
        print url, len(content)

    print

@defer.inlineCallbacks
def _timeit(f):
    startTime = time.time()
    ret = yield f()
    endTime = time.time()
    print 'Time: %f' % (endTime - startTime)
    defer.returnValue(ret)
    
@defer.inlineCallbacks
def run(urls):
    print 'downloadDeferredSerial'
    results = yield _timeit(lambda : downloadDeferredSerial(urls))
    _printResults(results)
    
    print 'downloadDeferredParallel'
    results = yield _timeit(lambda : downloadDeferredParallel(urls))
    _printResults(results)

    print 'downloadMapSerial'
    results = yield _timeit(lambda : downloadMapSerial(urls))
    _printResults(results)

    print 'downloadDeferWorkQueue'
    results = yield _timeit(lambda : downloadDeferWorkQueue(urls))
    _printResults(results)

    print 'downloadDeferredSerialInline'
    results = yield _timeit(lambda : downloadDeferredSerialInline(urls))
    _printResults(results)


def main():
    def _run():
        d = run(URLS)
        d.addCallback(lambda _ : reactor.stop())

        def _error(f):
            log.err(f)
            reactor.stop()
            
        d.addErrback(_error)
        return d

    reactor.callLater(0.0, _run)
    reactor.run()


if __name__ == '__main__':
    main()
    

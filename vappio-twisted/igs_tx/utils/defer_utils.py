import time

from twisted.internet import defer
from twisted.internet import reactor

from twisted.python import failure
from twisted.python import log

from igs.utils import logging

def mapPar(f, iterable, parallel=1):
    """
    Takes a function, an iterable, and optional number
    of parallel tasks to perform.  Returns a list of
    results of applying f to the iterable.  The results
    are guaranteed to be in the same order as specified
    in the iterable
    """
    @defer.inlineCallbacks
    def _f(i, res, d, completed, errored):
        completed['running'] += 1
        try:
            if not errored:
                idx, item = i.next()
                res.append(None)
                try:
                    res[idx] = yield f(item)
                    completed['running'] -= 1
                    _f(i, res, d, completed, errored)
                except Exception, err:
                    if not errored:
                        errored.append(True)
                        d.errback(err)
        except StopIteration:
            if completed['running'] == 1:
                d.callback(res)

    i = iter(enumerate(iterable))
    res = []
    d = defer.Deferred()
    completed = {'running': 0}
    errored = []

    for _ in range(parallel):
        _f(i, res, d, completed, errored)

    return d

def mapSerial(f, iterable):
    return mapPar(f, iterable, parallel=1)


def fold(f, init, iterable):
    """
    Folds over an iterable where f returns a deferred.
    """
    d = defer.Deferred()

    i = iter(iterable)

    def _iterate(accum):
        try:
            item = i.next()
            fDefer = f(accum, item)
            fDefer.addCallback(lambda r : reactor.callLater(0, _iterate, r))
            fDefer.addErrback(d.errback)
        except StopIteration:
            d.callback(accum)
        except:
            d.errback(failure.Failure())

    _iterate(init)

    return d



def tryUntil(tries, f, onFailure=None, retry=None):
    """
    Try to call f tries times at most.  If f succeeds, return value, if f fails try again, if the number
    of attempts has been reached return the last failure.

    onFailure is a function that takes no parameters and is returns a deferred, this is run between attempts.

    retry is a function that takes the failure as input and returns True if we should retry and False if not.

    if onFailure or giveUp fail, the entire tryUntil fails without iterating.
    
    Returns a Deferred
    """
    d = defer.Deferred()

    def _try(tries):
        try:
            fDefer = f()
            fDefer.addCallback(d.callback)
            
            def _failed(f):
                if tries > 0:
                    if retry:
                        retryDefer = retry(f)
                    else:
                        retryDefer = defer.succeed(True)


                    def retryOrGiveUp(r):
                        if r and onFailure:
                            return onFailure().addCallback(lambda _ : reactor.callLater(0, _try, tries - 1))
                        elif r:
                            return defer.succeed(True).addCallback(lambda _ : reactor.callLater(0, _try, tries - 1))
                        else:
                            d.errback(f)

                    retryDefer.addCallback(retryOrGiveUp)
                    retryDefer.addErrback(d.errback)
                else:
                    d.errback(f)
                    
            fDefer.addErrback(_failed)
        except:
            if tries > 0:
                _try(tries - 1)
            else:
                d.errback(failure.Failure())

    _try(tries)
    return d



def sleep(seconds):
    """Returns a deferred that will be fired after 'seconds'"""
    def _():
        d = defer.Deferred()
        reactor.callLater(seconds, d.callback, None)
        return d
    return _



def timeIt(f):
    """Times how long it takes the function returning the deferred to complete and prints it"""
    

    def _(*args, **kwargs):
        startTime = time.time()
        
        def _timeAndReturn(v):
            endTime = time.time()
            if logging.DEBUG:
                log.msg('TIMEIT: %s.%s %f' % (f.__module__,
                                              f.__name__,
                                              endTime - startTime))
            return v
        
        d = f(*args, **kwargs)
        d.addCallback(_timeAndReturn)
        return d

    return _

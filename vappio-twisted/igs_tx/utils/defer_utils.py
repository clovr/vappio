from twisted.internet import defer
from twisted.internet import reactor

from twisted.python import failure

def mapSerial(f, iterable):
    """
    Take an iterable and a function and iterate over it in serial calling f returning a list
    of the result of f.  If any call to f throws an exception the entire operation fails.

    This returns a Deferred
    """
    d = defer.Deferred()

    i = iter(iterable)
    res = []
    def _iterate():
        try:
            item = i.next()
            fDefer = f(item)
            fDefer.addCallback(lambda r : res.append(r))
            fDefer.addCallback(lambda _ : _iterate())
            fDefer.addErrback(d.errback)
        except StopIteration:
            d.callback(res)
        except:
            d.errback(failure.Failure())

    _iterate()
    return d
    


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
            fDefer.addCallback(lambda r : _iterate(r))
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




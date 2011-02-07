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
            d.errback(failuare.Failure())

    _iterate()
    return d
    

    

def tryUntil(tries, f, onFailure=None):
    """
    Try to call f tries times at most.  If f succeeds, return value, if f fails try again, if the number
    of attempts has been reached return the last failure.

    Returns a Deferred
    """
    d = defer.Deferred()

    def _try(tries):
        try:
            fDefer = f()
            fDefer.addCallback(d.callback)
            
            def _failed(f):
                if tries > 0:
                    if onFailure:
                        onFailureDefer = onFailure()
                    else:
                        onFailureDefer = defer.succeed(True)

                    onFailureDefer.addCallback(lambda _ : _try(tries - 1))
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


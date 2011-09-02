#
# This module offers the ability to compose/pipe functions where the evaluation of the piping
# can be short circuited at any point.  All of the functions must return a Deferred.  A
# `defer_pipe` is created with `defer_pipe.pipe` and `defer_pipe.compose`.  The resulting
# value is one that can be run with `defer_pipe.runPipe`.  All pipes take a single value
# as input.  The return value of each function will become the input to the next function.
#
# `defer_pipe.pipe` and `defer_pipe.compose` are the same except for the order functions
# are evaluated.
# pipe([f1, f2]) == compose([f2, f1]) == lambda x : f2(f1(x))
#
# The feature that this offers over simple composition is the sequence of functions
# can be stopped at any time, returning that value.  This means simple branching
# can be expressed.
#
# For example, imagine you want to express the logic of reading a value from a cache
# or creating it and caching it if it does not exist.  For this example we will ignore
# the added layer of dealing with Deferreds, and integrate the concept in after:
#
# def readCache(n):
#     if n in cache:
#         return emit(cache[n])
#     else:
#         n
#
# def createValue(n):
#     return ret((n, doSomething()))
#
# def cacheValue((n, v)):
#     cache[n] = v
#     return ret(v)
#
# readOrAdd = pipe([readCache, createValue, cacheValue])
#
# With this, readOrAdd('hi') will first see that there is no
# value in the cache, create it and cache it and return it.
# on subsequent calls it will return the value in the cache.

from twisted.internet import defer

from twisted.python import failure

from igs_tx.utils import pipe as pipe_lib
from igs_tx.utils import defer_utils

def pipeToDeferPipe(p):
    """
    Takes a regular pipe and wraps it up so it can be run in defer_pipe.runPipe
    """
    def _(i):
        try:
            return defer.succeed(p(i))
        except:
            return defer.errback(failure.Failure())

    return _

def runPipe(m, initialValue):
    def extractReturnValue(f):
        f.trap(pipe_lib.ReturnValue)
        try:
            f.raiseException()
        except pipe_lib.ReturnValue, retv:
            return retv.ret
        
    return m(initialValue).addErrback(extractReturnValue)

def runPipeCurry(m):
    return lambda initialValue : runPipe(m, initialValue)

def pipe(fs):
    def _runf(a, f):
        return defer.maybeDeferred(f, a)
    
    def _(v):
        return defer_utils.fold(_runf, v, fs)

    return _

def compose(fs):
    fs = list(fs)
    fs.reverse()
    return pipe(fs)


emit = pipe_lib.emit

def ret(v):
    return defer.succeed(v)

def fail(f):
    return defer.fail(f)

def emitDeferred(d):
    """
    Like emit but this takes a deferred and waits
    for it to finish then emits that value
    """
    return d.addCallback(lambda r : emit(r))

def const(c):
    """
    Shorthand for lambda c : lambda _ : ret(c)
    """
    return lambda _ : ret(c)

def hookError(f, onError):
    """
    Returns a function which calls f (which must return a deferred) and adds an errback
    which will call onError (which must return a deferred) and propogate the original error
    up.

    If an error happens in onError, that is what will be raised
    """
    def _handleError(f, *args, **kwargs):
        try:
            f.raiseException()
        except pipe_lib.ReturnValue:
            raise
        except:
            d = onError(f, *args, **kwargs)
            # "reraise" it
            d.addCallback(lambda _ : f)
            return d

    def _(*args, **kwargs):
        d = f(*args, **kwargs)
        d.addErrback(_handleError, *args, **kwargs)
        return d

    return _

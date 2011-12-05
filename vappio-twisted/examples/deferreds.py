# Most callback-based frameworks, such as NodeJS and Tornado, handle events
# using callback functions.  For example if you want to download a webpage
# you would do:
#
# downloadWebpage(url, function (contents) { /* handle page downloaded */ })
#
# In Twisted, downloadWebpage would return a Deferred to which you would add
# a callback, in pseudo code something like:
# d = downloadWebpage(url)
# d.addCallback(function(contents) { /* handle page downlaoded */ })
#
# At the lowest level, Twisted has callbacks but a library exposes control
# flow through deferreds rather than callbacks.  A user of a library would
# almost never pass in a function to call upon an event, rather they call
# a function and a Deferred is returned from that function, callbacks
# can then be added to that Deferred.
#
# It should be noted that Deferreds are not magic, they are not aware of
# asynchronous events or anything.  They are solely a mechanism for describing
# how data should move through some control flow.  You don't even actually have
# to use Twisted to make use of the behavior of Deferreds. All of these examples
# will, though.
import time

from twisted.internet import reactor
from twisted.internet import defer

from twisted.python import log

# Example 1: Make a function that sleeps for some amount of time
# Note that this function will return immediatly, but it is the
# firing of the deferred that is being delayed
def sleep(duration):
    # Create a deferred that will be returned
    d = defer.Deferred()
    # Tell the reactor to schedule the callback method of d to be
    # called after duration, call it with None.  The callback
    # method takes a value but in this case we don't need one
    # since we are just trying to wait some period of time
    reactor.callLater(duration, d.callback, None)
    # Return d
    return d

def useSleep():
    print 'Sleeping'
    d = sleep(10)

    def _print(_):
        print 'Waking'

    d.addCallback(_print)

    return d


# Example 2: The output of one callback becomes the input to the next
# callback.
def chaining():
    d = defer.Deferred()
    d.addCallback(lambda x : x + 1)
    d.addCallback(lambda x : x * 2)
    d.addCallback(lambda x : x - 1)

    def _print(x):
        print x
        return x

    d.addCallback(_print)
    
    d.callback(1)
    
    return d
    
    
# Example 3: Deferreds check to see if the previous callback returned
# a Deferred and will add themselves to its callback.  A callback can
# return a Deferred and the behavior is what one would expect.  The output
# of the nested Deferred will become the input to the next callback.

# In this exampple sleep returns a Deferred that will be fired
# at the end of a duration. We are adding 2 more sleeps to that Deferred
# so the entire Deferred will not be fired until the last 3 second sleep is
# done.
def sleepABunch():
    print 'Sleeping'
    d = sleep(1).addCallback(lambda _ : sleep(2)).addCallback(lambda _ : sleep(3))

    def _print(_):
        print 'Waking'
        
    d.addCallback(_print)
    return d
    
    

# Example 4: Deferreds handle both success and errors.  Add success handlers with
# .addCallback and add failure handlers with .addErrback.  A Deferred will capture any
# Exception thrown in it and wrap it in a Failure object and give it to the next errback
# in line.  This mimics how exception handling works.
def errorHandling():
    def _callback(x):
        print 'Callback', x
        return x + 1

    def _causeError(x):
        raise Exception('Causing exception at callback %d' % x)

    def _handleError(f):
        log.err(f)
        return 0

    def _dontHandleError(f):
        log.err(f)
        return f

    d = defer.Deferred()
    d.addCallback(_callback)
    d.addCallback(_callback)
    d.addCallback(_callback)
    d.addCallback(_causeError)
    d.addErrback(_handleError)
    d.addCallback(_callback)
    d.addErrback(_handleError)
    d.addCallback(_causeError)
    d.addErrback(_dontHandleError)
    d.addErrback(_handleError)

    d.callback(0)
    
    return d


# Example 5: Writing all this callback-based code is terrible, but Twisted
# provides a trick using decorators and generators make it a bit easier
@defer.inlineCallbacks
def inlined():
    print 'Sleeping'
    # We can call something that returns a deferred with yield
    yield sleep(3)
    print 'Waking'

    print 'Calling chaining'
    # yield can also return a value so we can get responses as well
    value = yield chaining()
    print 'Chaining returned', value

    # This is not valid though:
    # value = yield chaining() + yield chaining()

# Example 6: Because inlineCallbacks make use of generators, and generators
# cannot return a value, we have to use a special function to return
# a value from an inlined callback
@defer.inlineCallbacks
def inlinedReturn():
    @defer.inlineCallbacks
    def _inlinedReturn():
        value1 = yield chaining()
        value2 = yield chaining()

        # This will return the sum of the two values
        defer.returnValue(value1 + value2)

    ret = yield _inlinedReturn()
    print ret

@defer.inlineCallbacks
def _timeit(f):
    startTime = time.time()
    ret = yield f()
    endTime = time.time()
    print 'Time: %f' % (endTime - startTime)
    defer.returnValue(ret)
    
@defer.inlineCallbacks
def run():
    print 'Example 1'
    yield _timeit(lambda : useSleep())
    print
    
    print 'Example 2'
    yield _timeit(lambda : chaining())
    print

    print 'Example 3'
    yield _timeit(lambda : sleepABunch())
    print

    print 'Example 4'
    yield _timeit(lambda : errorHandling())
    print

    print 'Example 5'
    yield _timeit(lambda : inlined())
    print

    print 'Example 6'
    yield _timeit(lambda : inlinedReturn())
    print
    
def main():
    def _run():
        d = run()
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

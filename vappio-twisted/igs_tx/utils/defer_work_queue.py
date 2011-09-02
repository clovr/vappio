#
# This is a queue that takes functions that return a deferred and runs N in parallel
from twisted.internet import defer

from twisted.python import log

from igs.utils import dependency

class DeferWorkQueue(dependency.Dependable):
    """
    By default serializes work
    """
    
    def __init__(self, parallel=1):
        dependency.Dependable.__init__(self)
        
        self.parallel = parallel
        self.work = []
        self.running = 0

    def add(self, work, *args, **kwargs):
        self.work.append((work, args, kwargs))
        self._runWork()

    def extend(self, works):
        self.work.extend([(w, [], {}) for w in works])
        self._runWork()


    def _runWork(self):
        def _nextWork(_):
            self.running -= 1
            self._runWork()
        
        if self.running < self.parallel and self.work:
            while self.running < self.parallel and self.work:
                work, args, kwargs = self.work.pop(0)
                d = defer.maybeDeferred(work, *args, **kwargs)
                self.running += 1
                d.addErrback(lambda f : log.err(f))
                d.addCallback(_nextWork)

        self.changed('running', self.running)
        

def waitForCompletion(dwq):
    d = defer.Deferred()
    
    class _Waiter:
        def __init__(self):
            dwq.addDependent(self)
            
        def update(self, who, _aspect, value):
            if value == 0:
                d.callback(None)
                dwq.removeDependent(self)

    if dwq.running:
        _Waiter()
    else:
        d.callback(None)

    return d

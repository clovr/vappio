import array, struct, signal, traceback, time, StringIO

from twisted.internet import task
from twisted.python import log

try:
    # First try py-itimer from http://www.cute.fi/~torppa/py-itimer/
    import itimer as py_itimer
except ImportError:
    # Otherwise use the dl module
    import dl
    def itimer(seconds, libc=dl.open('libc.so.6')):
        sec = int(seconds)
        msec = int((seconds - sec) * 1e6)
        timeval = array.array('I', [0, 0, sec, msec])
        if libc.call('setitimer', 0, timeval.buffer_info()[0], 0) == -1:
            raise RuntimeError("Who knows what")
else:
    # Hooray
    def itimer(seconds):
        py_itimer.setitimer(0, seconds, 0)

class BigTimesliceTimer(object):
    lc = None
    lastRan = None
    _stack = None

    def start(self, precision=0.01):
        assert self.lc is None
        self.precision = precision
        signal.signal(signal.SIGALRM, self._signal)
        itimer(precision * 1.1)
        self.lc = task.LoopingCall(self._run)
        self.lc.start(precision).addErrback(self._ebLoop)


    def stop(self):
        self.lc.stop()
        del self.lc


    def _ebLoop(self, err):
        log.msg("BigTimesliceTimer broke")
        log.err(err)


    def _run(self):
        now = time.time()
        if self._stack is not None:
            print self._stack
            self._stack = None
        self.lastRan = now
        signal.signal(signal.SIGALRM, self._signal)
        itimer(self.precision * 1.1)
        

    def _signal(self, signum, frame):
        s = StringIO.StringIO()
        traceback.print_stack(file=s)
        self._stack = '\n'.join(s.getvalue().splitlines()[:-2])


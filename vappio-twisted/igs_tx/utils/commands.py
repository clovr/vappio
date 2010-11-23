#
# A rewrite of what igs.utils.commands, it really just boils down to 1 sane function
import os

from twisted.internet import reactor
from twisted.internet import protocol
from twisted.internet import defer

from igs.utils import functional as func

class NonInteractiveProcessProtocol(protocol.ProcessProtocol):
    """
    This is designed around, perhaps, sending some data to a process
    then writing the result back.

    When the process terminated self.deferred is fired.  If expect code
    is in self.expected then it is a success otherwise a failure
    """

    def __init__(self, stdoutf, stderrf, expected, initialText=None):
        self.deferred = defer.Deferred()
        self.initialText = initialText
        self.stdoutf = stdoutf
        self.stderrf = stderrf
        self.expected = expected

    def connectionMade(self):
        if self.initialText:
            self.transport.write(self.initialText)

        self.transport.closeStdin()

    def outReceived(self, data):
        if self.stdoutf:
            self.stdoutf(data)
        
    def errReceived(self, data):
        if self.stderrf:
            self.stderrf(data)

    def inConnectionLost(self):
        # We closed this, so ignore
        pass
    
    def outConnectionLost(self):
        # They closed their stdout, ignore
        # Waiting for the program to finish now
        pass
        
    def errConnectionLost(self):
        # They closed stdout, ignore
        pass
        
    def processExited(self, reason):
        if reason.value.exitCode in self.expected:
            self.deferred.callback(reason.value)
        else:
            self.deferred.errback(reason.value)

    def processEnded(self, reason):
        # This function is basically deprecated, ignore
        pass


def runProcess(cmdArgs,
               stdoutf=None,
               stderrf=None,
               expected=None,
               initialText=None,
               addEnv=None,
               newEnv=None,
               workingDir=None,
               uid=None,
               gid=None):
    """
    The only required function is cmdArgs.  cmdArgs is a list of strings, cmdArgs[0] must be the executable.
    stdoutf and stderrf are functions that will be called with the input data.  There is no guarantee
    the input data will be line terminated
    expected is a list of integers that are valid exit codes for the application
    initialText is any text to be sent to the program before closing stdin on it
    addEnv allows one to add keys to the current applications environment
    newEnv specifies a totally new environment to run the child under.  The current applications env
    is the default value
    workingDir is what directory to run the child process in
    uid and gid are numeric user id and group id to run program as
    
    This returns a deferred which will be fired on program exit
    """

    if newEnv is None:
        newEnv = dict(os.environ)

    if addEnv:
        newEnv = func.updateDict(newEnv, addEnv)


    if expected is None:
        expected = [0]
        
    pp = NonInteractiveProcessProtocol(stdoutf=stdoutf,
                                       stderrf=stderrf,
                                       expected=expected,
                                       initialText=initialText)

    kwargs = {}
    if workingDir:
        kwargs['path'] = workingDir
    if uid:
        kwargs['uid'] = uid
    if gid:
        kwargs['gid'] = gid
        
    reactor.spawnProcess(pp,
                         executable=cmdArgs[0],
                         args=cmdArgs,
                         env=newEnv,
                         **kwargs)

    return pp.deferred

#
# A rewrite of what igs.utils.commands, it really just boils down to 1 sane function
import os
import StringIO

from twisted.internet import reactor
from twisted.internet import protocol
from twisted.internet import defer

from twisted.python import log as logger

from igs.utils import functional as func

class Error(Exception):
    pass

class ProgramRunError(Error):
    def __init__(self, cmd, stderr=None):
        self.cmd = cmd
        self.stderr = stderr

    def __str__(self):
        return 'Command %r failed with %s' % (self.cmd, self.stderr)

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
        pass
    
    def processEnded(self, reason):
        if reason.value.exitCode in self.expected:
            self.deferred.callback(reason.value)
        else:
            self.deferred.errback(reason.value)


def runProcess(cmdArgs,
               stdoutf=None,
               stderrf=None,
               expected=None,
               initialText=None,
               addEnv=None,
               newEnv=None,
               workingDir=None,
               uid=None,
               gid=None,
               log=False):
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

    cmdArgs = [str(c) for c in cmdArgs]
    
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

    if log:
        logger.msg('Running command: ' + ' '.join(cmdArgs))
        
    reactor.spawnProcess(pp,
                         executable=cmdArgs[0],
                         args=cmdArgs,
                         env=newEnv,
                         **kwargs)

    def _error(_):
        raise ProgramRunError(cmdArgs)
    
    pp.deferred.addErrback(_error)
    return pp.deferred

def shell(cmd):
    """
    Takes a command that is a string and turns it into an sh call so it doesn't
    have to be parsedin order to call runProcess.

    ex. shell('echo testing') -> ['/bin/sh', '-c', 'echo testing']
    """
    return ['/bin/sh', '-c', cmd]


@defer.inlineCallbacks
def getOutput(cmdArgs,
              expected=None,
              initialText=None,
              addEnv=None,
              newEnv=None,
              workingDir=None,
              uid=None,
              gid=None,
              log=False):
    stdout = StringIO.StringIO()
    stderr = StringIO.StringIO()

    try:
        yield runProcess(cmdArgs,
                         stdoutf=stdout.write,
                         stderrf=stderr.write,
                         expected=expected,
                         initialText=initialText,
                         addEnv=addEnv,
                         newEnv=newEnv,
                         workingDir=workingDir,
                         uid=uid,
                         gid=gid,
                         log=log)
        defer.returnValue({'stdout': stdout.getvalue(), 'stderr': stderr.getvalue()})
    except ProgramRunError:
        raise ProgramRunError(cmdArgs, stderr.getvalue())
    

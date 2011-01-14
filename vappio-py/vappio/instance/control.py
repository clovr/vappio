##
# Functions for controling an instance
from igs.utils.ssh import runSystemSSHA
from igs.utils.commands import ProgramRunError, runProgramRunner


##
# Cheap and evil but the WARNING from ssh is annoying
def wrapStream(f):
    def _(l):
        if f and 'WARNING: ENABLED NONE CIPHER' not in l:
            f(l)

    return _

def runSystemInstanceA(instance, cmd, stdoutf, stderrf, user=None, options=None, log=False):
    """
    Asynchronous function for running a command on an instance
    """

    # We need to wrap calls in runCmd.sh to get our environment
    return runSystemSSHA(instance['public_dns'], 'source clovrEnv.sh; ' + cmd, stdoutf, wrapStream(stderrf), user, options, log)


def runSystemInstance(*args, **kwargs):
    """
    Blocking version fo runSystemInstanceA
    """
    return runProgramRunner(runSystemInstanceA(*args, **kwargs))

def runSystemInstanceEx(*args, **kwargs):
    """
    Blocking and throws an exception on failure
    """
    pr = runSystemInstanceA(*args, **kwargs)
    exitCode = runProgramRunner(pr)
    if exitCode != 0:
        raise ProgramRunError(pr.cmd, exitCode)

    

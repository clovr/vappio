##
# Functions for controling an instance
from igs.utils.ssh import runSystemSSHA
from igs.utils.commands import ProgramRunError, runProgramRunner


def runSystemInstanceA(instance, cmd, stdoutf, stderrf, user=None, options=None, log=False):
    """
    Asynchronous function for running a command on an instance
    """

    # We need to wrap calls in runCmd.sh to get our environment
    return runSystemSSHA(instance.publicDNS, 'source clovrEnv.sh; ' + cmd, stdoutf, stderrf, user, options, log)


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

    

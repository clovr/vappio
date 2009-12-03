##
# Useful functions for doing things with ssh
from igs.utils.commands import ProgramRunError, ProgramRunner, runProgramRunnerEx

def runSystemSSHA(host, cmd, stdoutf, stderrf, user=None, options=None):
    """
    Asynchornous function for running a command through ssh
    """
    command = ['ssh']
    if user:
        host = user + '@' + host

    if options:
        command.append(options)

    command.append(host)

    command.append(quoteStr(cmd))

    return ProgramRunner(' '.join(command), stdoutf, stderrf)

def runSystemSSH(host, cmd, stdoutf, stderrf, user=None, options=None):
    """
    Blocking version of runSystemSSHA

    Returns the exit code
    """
    return runProgramRunner(runSystemSSHA(host, cmd, stdoutf, stderrf, user, options))


def runSystemSSHEx(host, cmd, stdoutf, stderrf, user=None, options=None):
    """
    Blocking version of runSystemSSHA, throws an exception on failure though
    """
    pr = runSystemSSHA(host, cmd, stdoutf, stderrf, user, options)
    exitCode = runProgramRunner(pr)
    if exitCode != 0:
        raise ProgramRunError(pr.cmd, exitCode)


def scpFromA(host, src, dst, user=None, options=None):
    """
    Asynchronous function to copy scp a file from a host
    """
    command = ['scp']
    if user:
        host = user + '@' + host

    if options:
        command.append(options)

    command.append(host + ':' + src)
    command.append(dst)

    return ProgramRunner(' '.join(command), stdoutf, stderrf)

def scpToA(host, src, dst, user=None, options=None):
    """
    Asynchronous function to copy scp a file to a host
    """
    command = ['scp']
    if user:
        host = user + '@' + host

    if options:
        command.append(options)

    command.append(src)
    command.append(host + ':' + dst)

    return ProgramRunner(' '.join(command), stdoutf, stderrf)

def scpFrom(host, src, dst, user=None, options=None):
    """
    Blocking function to copy scp a file from a host

    Returns the exit code
    """
    return runProgramRunner(scpFromA(host, src, dst, user, options))

def scpFromEx(host, src, dst, user=None, options=None):
    """
    Blocking function to copy scp a file from a host

    Throws an exception if it fails
    """
    pr = scpFromA(host, src, dst, user, options)
    exitCode = runProgramRunner(pr)
    if exitCode != 0:
        raise ProgramRunError(pr.cmd, exitCode)

def scpTo(host, src, dst, user=None, options=None):
    """
    Blocking function to copy scp a file to a host

    Returns the exit code
    """
    return runProgramRunner(scpToA(host, src, dst, user, options))

def scpToEx(host, src, dst, user=None, options=None):
    """
    Blocking function to copy scp a file to a host

    Throws an exception if it fails
    """
    pr = scpToA(host, src, dst, user, options)
    exitCode = runProgramRunner(pr)
    if exitCode != 0:
        raise ProgramRunError(pr.cmd, exitCode)    

from igs.utils import core

from igs_tx.utils import commands


def runProcessSSH(host, cmd, stdoutf, stderrf, sshUser=None, sshFlags=None, initialText=None, log=False, **kwargs):
    command = ['ssh']
    if sshUser:
        host = sshUser + '@' + host

    if sshFlags:
        command.append(sshFlags)

    command.append(host)

    command.append(core.quoteEscape(cmd))

    command = ' '.join(command)

    return commands.runProcess(commands.shell(str(command)),
                               stdoutf=stdoutf,
                               stderrf=stderrf,
                               initialText=str(initialText),
                               log=log,
                               **kwargs)

                               

def getOutput(host, cmd, sshUser=None, sshFlags=None, initialText=None, log=False, **kwargs):
    command = ['ssh']
    if sshUser:
        host = sshUser + '@' + host

    if sshFlags:
        command.append(sshFlags)

    command.append(host)

    command.append(core.quoteEscape(cmd))

    command = ' '.join(command)

    return commands.getOutput(commands.shell(str(command)),
                              initialText=str(initialText),
                              log=log,
                               **kwargs)

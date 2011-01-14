from igs.utils import core

from igs_tx.utils import commands


def runProcessSSH(host, cmd, stdoutf, stderrf, sshUser=None, sshFlags=None, initialText=None, log=False):
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
                               log=log)

                               

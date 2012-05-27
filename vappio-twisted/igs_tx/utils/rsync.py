from twisted import python

from igs_tx.utils import commands


def rsyncTo(host, src, dst, files=None, options=None, user=None, log=False):
    """
    Transfers `files` from `host` in directory `src` to directory `dst`.  If
    `files` is None then it is assumed `src` is the complete path to be copied
    otherwise it is believed to be a list of files in `src`.
    """
    cmd = ['rsync']
    if files:
        cmd.append('--files-from=-')
        initialText = '\n'.join(files)
    else:
        initialText = None
        
    if options:
        cmd.append(options)

    if user:
        host = user + '@' + host

    cmd.extend([src, host + ':' + dst])

    return commands.runProcess(commands.shell(str(' '.join(cmd))),
                               expected=[0, 23],
                               stderrf=python.log.err,
                               initialText=str(initialText),
                               log=log)
    
def rsyncFrom(host, src, dst, files=None, options=None, user=None, log=False):
    """
    Copies `files` from `host` in location `src` to the local `dst`.  If `files`
    is None then `src` is assumed to be the actual path to copy.
    """
    cmd = ['rsync']
    if files:
        cmd.append('--files-from=-')
        initialText = '\n'.join(files)
    else:
        initialText = None
        
    if options:
        cmd.append(options)

    if user:
        host = user + '@' + host

    cmd.extend([host + ':' + src, dst])

    return commands.runProcess(commands.shell(str(' '.join(cmd))),
                               expected=[0, 23],
                               stderrf=python.log.err,
                               initialText=str(initialText),
                               log=log)    


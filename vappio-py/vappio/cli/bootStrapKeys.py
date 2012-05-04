#!/usr/bin/env python
##
# Temporary program for loading keys into the proper location
import os
import sys

from igs.utils.cli import buildConfigN
from igs.utils.functional import identity

from igs.utils.commands import runSystemEx, runSingleProgramEx

OPTIONS = [
    ('devel', '-d', '--devel', 'Path to devel1.pem', identity)
    ]

def writeKeyData(authKeysPath, keyData, user):
    fout = open(authKeysPath, 'a')
    fout.write('\n' + keyData + '\n')
    fout.close()
    runSingleProgramEx('chown %s:%s %s' % (user, user,authKeysPath), None, None)
    runSingleProgramEx('chmod 600 ' + authKeysPath, None, None)

def main(options, _args):
    if options('general.devel'):
        if not os.path.exists('/mnt/keys/devel1.pem'):
            runSystemEx('cp %s /mnt/keys' % options('general.devel'))
    else:
        if not os.path.exists('/mnt/keys/devel1.pem'):
            runSingleProgramEx('ssh-keygen -f /mnt/keys/devel1.pem -P ""', None, None)

    keyData = []
    runSingleProgramEx('ssh-keygen -y -f /mnt/keys/devel1.pem', keyData.append, sys.stderr.write)
    keyData = ''.join(keyData)

    for path, user in [('/root', 'root'), ('/home/www-data', 'www-data')]:
        authorizedKeysPath = os.path.join(path, '.ssh', 'authorized_keys')
        runSingleProgramEx('mkdir -p %s' % os.path.dirname(authorizedKeysPath), None, None)

        if os.path.exists(authorizedKeysPath):
            authorizedKeys = open(authorizedKeysPath).read()
            if keyData not in authorizedKeys:
                writeKeyData(authorizedKeysPath, keyData)
        else:
            writeKeyData(authorizedKeysPath, keyData, user)

    print
    print
    print 'Setup complete.'
    print '*** Remember, currently you have to do this every time you restart the VM'

    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

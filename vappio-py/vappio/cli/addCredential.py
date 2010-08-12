#!/usr/bin/env python
import os
from twisted.python import reflect

from igs.utils import commands
from igs.utils import cli
from igs.utils import functional as func

from vappio.credentials import manager

OPTIONS = [
    ('cred_name', '', '--cred-name', 'Name of the credential', cli.notNone),
    ('cred_desc', '', '--desc', 'Description of the credential', cli.defaultIfNone('')),
    ('ctype', '', '--ctype', 'Cluster type this cert is for (ec2, eucalyptus, local)', func.compose(cli.restrictValues(['ec2', 'eucalyptus', 'local']),
                                                                                                    cli.defaultIfNone('local'))),
    ('cert', '-c', '--cert', 'Path to cert', func.identity),
    ('pkey', '-p', '--pkey', 'path to private key', func.identity),
    ('devel', '-d', '--devel', 'Path to devel1.pem', func.identity),    
    ('metadata', '-m', '',
     'Add metadata in a key=value notation.  Multiple options are valid.  Ex: -m ec2_url=http://foo/bar/zoom -m comment="This works"',
     cli.defaultIfNone([]),
     cli.LIST)
    ]


def main(options, _args):

    # Setup the cert if the user gave the options
    if options('general.cert') and options('general.pkey'):
        manager.saveCredential(manager.createCredential(options('general.cred_name'),
                                                        options('general.cred_desc'),
                                                        reflect.namedAny('vappio.' + options('general.ctype') + '.control'),
                                                        options('general.cert') and open(options('general.cert')).read(),
                                                        options('general.pkey') and open(options('general.pkey')).read(),
                                                        True,
                                                        dict([s.split('=', 1) for s in options('general.metadata')])))
        
    # Setup devel1.pem
    if options('general.devel'):
        if not os.path.exists('/mnt/keys/devel1.pem'):
            commands.runSystemEx('cp %s /mnt/keys' % options('general.devel'))
    else:
        if not os.path.exists('/mnt/keys/devel1.pem'):
            commands.runSingleProgramEx('ssh-keygen -f /mnt/keys/devel1.pem -P ""', None, None)
            
    keyData = []
    commands.runSingleProgramEx('ssh-keygen -y -f /mnt/keys/devel1.pem', keyData.append, None)
    keyData = ''.join(keyData)

    authorizedKeys = open('/root/.ssh/authorized_keys').read()
    if keyData not in authorizedKeys:
        fout = open('/root/.ssh/authorized_keys', 'a')
        fout.write(keyData + '\n')
        fout.close()

    

if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))
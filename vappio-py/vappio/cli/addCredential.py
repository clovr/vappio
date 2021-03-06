#!/usr/bin/env python
from twisted.python import reflect

from igs.utils import cli
from igs.utils import functional as func

from vappio.webservice import credential

from vappio.tasks.utils import runTaskStatus

from vappio.credentials import manager


OPTIONS = [
    ('cred_name', '', '--cred-name', 'Name of the credential', cli.notNone),
    ('cred_desc', '', '--desc', 'Description of the credential', cli.defaultIfNone('')),
    ('ctype', '', '--ctype', 'Cluster type this cert is for (ec2, nimbus, diag, adhoc, local)',
     cli.restrictValues(['diag', 'nimbus', 'ec2', 'local', 'adhoc'])),
    ('cert', '-c', '--cert', 'Path to cert', func.identity),
    ('pkey', '-p', '--pkey', 'path to private key', func.identity),
    ('devel', '-d', '--devel', 'Path to devel1.pem', func.identity),    
    ('metadata', '-m', '',
     ('Add metadata in a key=value notation.  Multiple options are valid.  '
      'Ex: -m ec2_url=http://foo/bar/zoom -m comment="This works"'),
     cli.defaultIfNone([]),
     cli.LIST),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end',
     cli.defaultIfNone(False), cli.BINARY)    
    ]


def main(options, _args):

    # Setup the cert if the user gave the options
    if options('general.cert') and options('general.pkey'):
        taskName = credential.saveCredential('localhost',
                                             'local',
                                             options('general.cred_name'),
                                             options('general.cred_desc'),
                                             options('general.ctype'),
                                             (options('general.cert') and
                                              open(options('general.cert')).read()),
                                             (options('general.pkey') and
                                              open(options('general.pkey')).read()),
                                             dict([s.split('=', 1)
                                                   for s in options('general.metadata')]))
        if options('general.print_task_name'):
            print taskName
        else:
            runTaskStatus(taskName)

        

if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))

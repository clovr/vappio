#!/usr/bin/env python

from igs.utils import cli
from igs.utils import functional as func

from vappio.webservice import credential


OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', cli.defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', cli.defaultIfNone('local')),
    ('cred_name', '', '--cred-name', 'Name of credential, all credentials are listed if not provided', func.identity)
    ]
    

def main(options, _args):
    cred = credential.loadCredentials(options('general.host'), options('general.name'))

    if options('general.cred_name'):
        cred = [c for c in cred if c.name == options('general.cred_name')]

    print '\n'.join(['\t'.join(['CRED', c.name]) for c in cred])


if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))

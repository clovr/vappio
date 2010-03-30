#!/usr/bin/env python
##
# Temporary program for loading keys into the proper location
import os

from igs.utils.cli import buildConfigN, notNone
from igs.utils.functional import identity

from igs.utils.commands import runSystemEx

from vappio.ec2.control import listKeypairs, addKeypair, listGroups, addGroup, authorizeGroup

OPTIONS = [
    ('cert', '-c', '--cert', 'Path to cert', identity),
    ('pk', '-p', '--pk', 'Path to private key', identity),
    ('devel', '-d', '--devel', 'Path to devel1.pem', identity)
    ]

def main(options, _args):
    if options('general.cert') and options('general.pk'):
        runSystemEx('cp %s /tmp/ec2-cert.pem' % options('general.cert'))
        runSystemEx('cp %s /tmp/ec2-pk.pem' % options('general.pk'))
        runSystemEx('chmod +r /tmp/*.pem')
        if 'vappio_00' not in listKeypairs():
            addKeypair('vappio_00')

        groups = listGroups()
        if 'vappio' not in groups:
            print 'We need to setup your EC2 group information.  In order to do this we need',
            print 'your Amazon account number.  This is a number that is around 12 digits in length.',
            print 'We are not recording this value in any way, simply using it to properly create',
            print 'security groups'
            accountNumber = raw_input('Account number: ')
            ##
            # Setup vappio group
            addGroup('vappio', 'Ports for internal comm between vappio hosts')
            authorizeGroup('vappio',
                           'tcp',
                           (1, 65535),
                           'vappio',
                           accountnumber)
            authorizeGroup('vappio',
                           'udp',
                           (1, 65535),
                           'vappio',
                           accountnumber)
            authorizeGroup('vappio',
                           'icmp',
                           (-1, -1),
                           'vappio',
                           accountnumber)
            authorizeGroup('vappio',
                           'tcp',
                           22)

            ##
            # Setup web group
            addGroup('web', 'Public ports')
            for port in [22, 80, 443, 1555, 2222, 8004, 8080, 50030, 50070]:
                authorizeGroup('web',
                               'tcp',
                               port)
    else:
        print 'This image will not be EC2 enabled (you must specify --cert and --pk to enable it).'
        print 'See --help for more information'

        
    if options('general.devel'):
        if not os.path.exists('/mnt/keys/devel1.pem'):
            runSystemEx('cp %s /mnt/keys' % options('general.devel'))
    else:
        if not os.path.exists('/mnt/keys/devel1.pem'):
            runSystemEx('ssh-keygen -f /mnt/keys/devel1.pem -P ""')

    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

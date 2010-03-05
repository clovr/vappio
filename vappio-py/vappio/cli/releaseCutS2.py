#!/usr/bin/env python
##
# Step 1 in cutting a release
# This runs on the build box
import sys
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.functional import identity
from igs.utils.config import replaceStr
from igs.utils.commands import runSystemEx



OPTIONS = [
    ('remote_name', '', '--remote-name', 'Name of remote machine the image lives on', notNone),
    ('image', '-i', '--image', 'Image to bundle', identity),
    ('cert', '-c', '--cert', 'Certifiate to use, default $EC2_CERT', defaultIfNone(os.getenv('EC2_CERT'))),
    ('key', '-k', '--key', 'Key to use, default $EC2_PRIVATE_KEY', defaultIfNone(os.getenv('EC2_PRIVATE_KEY'))),
    ('user', '-u', '--user', 'AWS account number, defaults to $EC2_ACCOUNT_ID', defaultIfNone(os.getenv('EC2_ACCOUNT_ID'))),
    ('access_key', '', '--access_key', 'AWS access key, defaults to $EC2_ACCESS_KEY', defaultIfNone(os.getenv('EC2_ACCESS_KEY'))),
    ('secret_access_key', '', '--secret_access_key', 'AWS secret access key, defaults to $EC2_SECRET_ACCESS_KEY',
     defaultIfNone(os.getenv('EC2_SECRET_ACCESS_KEY'))),
    ('dest', '-d', '--dest', 'Destination', notNone),
    ('ec2cert', '', '--ec2cert', 'EC2 cert to use', identity),
    ('kernel', '', '--kernel', 'What AKI to use', defaultIfNone('aki-fd15f694')),
    ('arch', '-r', '--arch', 'Architecture (i386 or x86_64)', identity),
    ('debug', '', '--debug', 'Display debugging information', identity, True),    
    ]


def waitForPasswordChange():
    sys.stdout.write('Have you changed the password on the image? (Y/N): ')
    sys.stdout.flush()
    res = sys.stdin.readline().strip()
    while res != 'Y':
        sys.stdout.write('(Y/N)')
        sys.stdout.flush()
        res = sys.stdin.readline().strip()
        

def main(options, _args):
    runSystemEx('scp %s:/export/%s .' % (options('general.remote_name'), options('general.image')), log=True)
    runSystemEx('cp %s /usr/local/projects/clovr/images' % options('general.image'), log=True)
    runSystemEx('cp %s VMware_conversion/' % options('general.image'), log=True)

    waitForPasswordChange()
    
    cmd = ['ec2-bundle-image',
           '-c ${general.cert}',
           '-k ${general.key}',
           '-u ${general.user}',
           '--kernel ${general.kernel}',
           '-i ${general.image}',
           '-d ${general.dest}',
           '-p ${general.image}',
           '-r ${general.arch}']

    if options('general.ec2cert'):
        cmd.append('--ec2cert ${general.ec2cert}')

    runSystemEx(replaceStr(' '.join(cmd), options), log=options('general.debug'))

    cmd = ['ec2-upload-bundle', '-b ${general.image}', '-m ${general.dest}/${general.image}.manifest.xml', '-a ${general.access_key}', '-s ${general.secret_access_key}']
    runSystemEx(replaceStr(' '.join(cmd), options), log=options('general.debug'))

    cmd = ['ec2-register', '${general.image}/${general.image}.manifest.xml', '-K ${general.key}', '-C ${general.cert}']

    ##
    # We want to output the AMI regardless
    runSystemEx(replaceStr(' '.join(cmd), options), log=True)



if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

#!/usr/bin/env python
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.config import configFromMap, replaceStr
from igs.utils.commands import runSystemEx
from igs.utils.functional import identity


OPTIONS = [
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


def main(options, _args):
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

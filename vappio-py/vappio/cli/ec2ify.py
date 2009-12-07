#!/usr/bin/env python
import os
import optparse

from igs.utils.cli import buildConfig, MissingOptionError
from igs.utils.config import configFromMap, replaceStr
from igs.utils.commands import runSystemEx

def cliParser():
    parser = optparse.OptionParser()    

    parser.add_option('-i', '--image', dest='image', help='Image to bundle')
    parser.add_option('-c', '--cert', dest='cert', help='Certificate to use, default $EC2_CERT')
    parser.add_option('-k', '--key', dest='key', help='Key to use, default $EC2_PRIVATE_KEY')
    parser.add_option('-u', '--user', dest='user', help='AWS account number, defaults to $EC2_ACCOUNT_ID')
    parser.add_option('', '--access_key', dest='access_key', help='AWS access key, defaults to $EC2_ACCESS_KEY')
    parser.add_option('', '--secret_access_key', dest='secret_access_key', help='AWS secret access key, defaults to $EC2_SECRET_ACCESS_KEY')
    parser.add_option('-d', '--dest', dest='dest', help='Destination')
    parser.add_option('', '--ec2cert', dest='ec2cert', help='EC2 cert to use')
    parser.add_option('', '--debug', dest='debug', default=False, action='store_true', help='Display debugging information')
    parser.add_option('', '--kernel', dest='kernel', default='aki-fd15f694',
                      help='What AKI to use')
    parser.add_option('-r', '--arch', dest='arch', help='Architecture (i386 or x86_64)')

    return parser


def cliMerger(cliOptions, _args):
    for i in ['image', 'dest', 'arch']:
        if not hasattr(cliOptions, i) or getattr(cliOptions, i) is None:
            raise MissingOptionError('Missing option: ' + i)

    for e, i in [('EC2_CERT', 'cert'), ('EC2_PRIVATE_KEY', 'key'), ('EC2_ACCOUNT_ID', 'user'),  ('EC2_ACCESS_KEY', 'access_key'), ('EC2_SECRET_ACCESS_KEY', 'secret_access_key')]:
        if not hasattr(cliOptions, i) or getattr(cliOptions, i) is None:
            if not os.getenv(e):
                raise MissingOptionError('Missing options: ' + i)
            else:
                setattr(cliOptions, i, os.getenv(e))

    return configFromMap({
        'image': cliOptions.image,
        'cert': cliOptions.cert,
        'key': cliOptions.key,
        'user': cliOptions.user,
        'dest': cliOptions.dest,
        'ec2cert': cliOptions.ec2cert,
        'debug': cliOptions.debug,
        'kernel': cliOptions.kernel,
        'arch': cliOptions.arch,
        'access_key': cliOptions.access_key,
        'secret_access_key': cliOptions.secret_access_key
        })


def main(options):
    cmd = ['ec2-bundle-image', '-c ${cert}', '-k ${key}', '-u ${user}', '--kernel ${kernel}', '-i ${image}', '-d ${dest}', '-p ${image}', '-r ${arch}']
    if options('ec2cert'):
        cmd.append('--ec2cert ${ec2cert}')

    runSystemEx(replaceStr(' '.join(cmd), options), log=options('debug'))

    cmd = ['ec2-upload-bundle', '-b ${image}', '-m ${dest}/${image}.manifest.xml', '-a ${access_key}', '-s ${secret_access_key}']
    runSystemEx(replaceStr(' '.join(cmd), options), log=options('debug'))

    cmd = ['ec2-register', '${image}/${image}.manifest.xml', '-K ${key}', '-C ${cert}']
    runSystemEx(replaceStr(' '.join(cmd), options), log=options('debug'))


if __name__ == '__main__':
    options = buildConfig(cliParser(), cliMerger)
    main(options)

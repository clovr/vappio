#!/usr/bin/env python
##
# Step 1 in cutting a release
# This runs on the build box
import sys
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.functional import identity
from igs.utils import config
from igs.utils.commands import runSystemEx, runSingleProgramEx
from igs.utils.logging import logPrint, errorPrint
from igs.threading import threads


OPTIONS = [
    ('version', '', '--version', 'Version of this release', notNone),
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
        

def bundleAMI(chan):
    options, rchan = chan.receive()
    try:
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
            
        runSystemEx(config.replaceStr(' '.join(cmd), options), log=options('general.debug'))
            
        cmd = ['ec2-upload-bundle', '-b ${general.image}', '-m ${general.dest}/${general.image}.manifest.xml', '-a ${general.access_key}', '-s ${general.secret_access_key}']
        runSystemEx(config.replaceStr(' '.join(cmd), options), log=options('general.debug'))
        
        cmd = ['ec2-register', '${general.image}/${general.image}.manifest.xml', '-K ${general.key}', '-C ${general.cert}']

        outp = []
        runSingleProgramEx(config.replaceStr(' '.join(cmd), options), stdoutf=outp.append, stderrf=sys.stderr.write, log=True)
        rchan.send(''.join(outp))
    except Exception, err:
        rchan.sendError(err)


def convertImage(chan):
    options, rchan = chan.receive()
    try:
        runSingleProgramEx('vmplayer VMware_conversion/conversion_image.vmx', stdoutf=None, stderrf=None, log=True)
        rchan.send(None)
    except Exception, err:
        rchan.sendError(err)
        
def main(options, _args):
    runSystemEx('svn copy https://clovr.svn.sourceforge.net/svnroot/clovr/trunk https://clovr.svn.sourceforge.net/svnroot/clovr/tags/%s -m "Cutting release %s"' % (options('general.version'), options('general.version')),
              log=True)
    runSystemEx('svn copy https://vappio.svn.sourceforge.net/svnroot/vappio/trunk https://vappio.svn.sourceforge.net/svnroot/vappio/tags/%s -m "Cutting release %s"' % (options('general.version'), options('general.version')),
              log=True)
    
    runSystemEx('scp %s:/export/%s .' % (options('general.remote_name'), options('general.image')), log=True)
    runSystemEx('cp %s /usr/local/projects/clovr/images' % options('general.image'), log=True)
    runSystemEx('cp %s VMware_conversion/shared/convert_img.img' % options('general.image'), log=True)


    convertChannel = threads.runThreadWithChannel(convertImage).channel.sendWithChannel(options)

    waitForPasswordChange()
    bundleChannel = threads.runThreadWithChannel(bundleAMI).channel.sendWithChannel(options)


    try:
      amiId = bundleChannel.receive()
      logPrint('AMI: ' + amiId)
    except Exception, err:
      amiId = None
      errorPrint('Bundling AMI failed for some reason.  Error message:')
      errorPrint(str(err))

    try:
        convertChannel.receive()
        vmWareDir = 'clovr-vmware.%s' % options('general.version')
        runSystemEx('mkdir -p ' + vmWareDir, log=True)
        runSystemEx('mv VMware_conversion/shared/converted_img.vmdk %s' % os.path.join(vmWareDir, 'clovr.9-04.x86-64.%s.vmdk' % options('general.version')))
        runSystemEx('mkdir -p %s %s' % (os.path.join(vmWareDir, 'keys'),
                                        os.path.join(vmWareDir, 'user_data')), log=True)
        runSystemEx('cp -rv /usr/local/projects/clovr/shared ' + vmWareDir, log=True)
        fout = open(os.path.join(vmWareDir, 'start_clovr.vmx'), 'w')
        clovrConf = config.configFromMap(dict(version=options('general.version')))
        for line in open('/usr/local/projects/clovr/start_clovr.vmx'):
            fout.write(config.replaceStr(line, clovrConf))
    except Exception, err:
        errorPrint('Converting image failed.  Error message:')
        errorPrint(str(err))



if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

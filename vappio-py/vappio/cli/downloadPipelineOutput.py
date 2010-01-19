#!/usr/bin/env python
##
# Uploads files to a cluster
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.ssh import scpFromEx
from igs.utils.logging import errorPrintS, errorPrint
from igs.utils.functional import compose

from vappio.instance.transfer import downloadPipeline
from vappio.instance.misc import getInstances

from vappio.ec2 import control as ec2control

OPTIONS = [
    ('conf', '', '--conf', 'Name of config file', notNone),
    ('name', '', '--name', 'Name of cluster (in this case the IP address of the master)', notNone),
    ##
    # Want to make sure this is an int but we want it as a string later int he program
    ('pipeline', '-p', '--pipeline_id', 'ID # for the pipeline', compose(str, int, notNone)),
    ('output_dir', '-o', '--output_dir', 'Directory the output file should go to', notNone),
    ('overwrite', '', '--overwrite', 'Do you want to overwrite a local file if it already exists?', defaultIfNone(False), True),
    ]


def main(options, _args):
    instances = getInstances(lambda i : i.publicDNS == options('general.name'), ec2control)
    if not instances:
        raise MissingOptionError('Did not provide a valid host')

    mastInst = instances[0]

    outF = '/mnt/%s_output.tar.gz' % options('general.pipeline')
    
    cmd = ['cd /mnt/projects/clovr;',
           'tar',
           '-zcf',
           outF,
           'output_repository/*/%s_default' % options('general.pipeline')]
    
    runSystemInstanceEx(mastInst, ' '.join(cmd), None, errorPrintS, user='root', options=options('ssh.options'), log=True)
    fileExists = os.path.exists(os.path.join(options('general.output_dir'), os.path.basename(outF)))
    if fileExists and options('general.overwrite') or not fileExists:
        scpFromEx(mastInst.publicDNS, outF, options('general.output_dir'), user='root', options=options('ssh.options'), log=True)
    else:
        errorPrint('')
        errorPrint('FAILING, File already exists and you have chosen not to overwrite')
        errorPrint('')

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

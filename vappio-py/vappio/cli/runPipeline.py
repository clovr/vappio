#!/usr/bin/env python
##
# This just hands the work off to a remote machine
import os

from igs.utils.cli import buildConfigN, MissingOptionError, notNone

from igs.utils.config import configFromMap, configFromStream
from igs.utils.logging import errorPrintS, logPrintS

from vappio.instance.control import runSystemInstanceEx

from vappio.cluster.persist import load, dump

OPTIONS = [
    ('name', '', '--name', 'Name of cluster', notNone),
    ('pipeline', '', '--pipeline', 'Name of pipeline', notNone),
    ]

def main(options, args):
    options = configFromMap({'general': {'options': args}}, options)
    
    cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))
        
    cmd = ['runPipeline_remote.py', options('general.pipeline')] + options('general.options')
    runSystemInstanceEx(cluster.master, ' '.join(cmd), logPrintS, errorPrintS, user='root', options=cluster.config('ssh.options'), log=True)    
        

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS, usage='usage: %prog --name x --pipeline y [ -- options for pipeline]'))

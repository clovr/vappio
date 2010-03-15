#!/usr/bin/env python
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone, restrictValues
from igs.utils.functional import identity
from igs.utils.commands import runSystemEx

from vappio.core.error_handler import runCatchError, mongoFail
from vappio.webservice.cluster import loadCluster
from vappio.tags.tagfile import realizePhantom, isPhantom, hasFiles, loadTagFile


OPTIONS = [
    ('tag_name', '', '--tag-name', 'Name of the tag', notNone),
    ]


    

def main(options, _args):
    cluster = loadCluster('localhost', 'local')
    ctype = cluster.config('general.ctype')
    tf = loadTagFile(os.path.join(cluster.config('dirs.tag_dir'), options('general.tag_name')))
    if not hasFiles(tf) and isPhantom(tf):
        outDir = os.path.join(cluster.config('dirs.upload_dir'), options('general.tag_name'))
        runSystemEx('mkdir -p ' + outDir)
        realizePhantom(ctype,
                       outDir,
                       tf)
        cmd = ['tagDataR.py',
               '--tag-name=' + options('general.tag_name'),
               '--tag-base-dir=' + outDir,
               ##
               # Want to be recursive regardless
               '-r', '-o'
               tf('phantom.cluster.%s.tag_options' % ctype),
               outDir]
        runSystemEx(' '.join(cmd))



if __name__ == '__main__':
    runCatchError(lambda : main(*buildConfigN(OPTIONS)),
                  mongoFail(dict(action='realizePhantom')))

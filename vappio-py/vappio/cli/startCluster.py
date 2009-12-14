#!/usr/bin/env python

import optparse

from igs.utils.cli import buildConfig
from igs.utils.config import configFromMap, configFromStream
from igs.utils.logging import logPrint

from vappio.cluster.control import Cluster
from vappio.ec2 import control as ec2Control


def cliParser():
    parser = optparse.OptionParser()

    parser.add_option('', '--conf', dest='conf', default=None,
                      help='Config file name')
    parser.add_option('', '--name', dest='name', default=None,
                      help='Name of cluster')
    parser.add_option('', '--num', dest='num', default=0, type='int',
                      help='Number of exec nodes to start')
    parser.add_option('', '--ctype', dest='ctype', default=None,
                      help='The type of cluster (ec2, nimbus)')
    parser.add_option('-d', '--dev_mode', dest='dev_mode', default=False,
                      action='store_true', help='Development mode or not')
    parser.add_option('', '--release_cut', dest='release_cut', default=False,
                      action='store_true', help='Want to cut a release')
    return parser

def cliMerger(cliOptions, _args):
    if not cliOptions.name:
        raise Exception('Must provide a name')
    if not cliOptions.ctype:
        raise Exception('Must provide a cluster type')
    if not cliOptions.conf:
        raise Exception('Must provide a config file')
    
    return configFromMap(dict(conf=cliOptions.conf,
                              name=cliOptions.name,
                              num=cliOptions.num,
                              ctype=cliOptions.ctype,
                              dev_mode=cliOptions.dev_mode,
                              release_cut=cliOptions.release_cut))



def main(options):
    conf = configFromStream(open(options('conf')), options)
    conf = configFromMap(
        {'cluster': {'master_groups': [f.strip() for f in conf('cluster.master_groups').split(',')],
                     'exec_groups': [f.strip() for f in conf('cluster.exec_groups').split(',')]
                     }
         }, conf)
    ctype = ec2Control
    cl = Cluster(options('name'), ctype, conf)
    cl.startCluster(options('num'), devMode=options('dev_mode'), releaseCut=options('release_cut'))
    logPrint('The master IP is: ' + cl.master.publicDNS)

    
if __name__ == '__main__':
    options = buildConfig(cliParser(), cliMerger)
    main(options)

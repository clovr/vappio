#!/usr/bin/env python

import optparse

from igs.utils.cli import MissingOptionError, buildConfigN, notNone
from igs.utils.config import configFromMap, configFromStream
from igs.utils.logging import logPrint

from vappio.cluster.control import Cluster
from vappio.ec2 import control as ec2Control


OPTIONS = [
    ('conf', '', '--conf', 'Config file name', notNone),
    ('name', '', '--name', 'Name of cluster (in this case public host name of master)', notNone),
    ('num', '', '--num', 'Number of nodes to create', int),
    ('ctype', '', '--ctype', 'Type of cluster', notNone),
    ]


def getInstances(f):
    return [i for i in ec2Control.listInstances() if f(i)]


def main(options, _args):
    options = configFromMap(
        {'cluster': {'master_groups': [f.strip() for f in options('cluster.master_groups').split(',')],
                     'exec_groups': [f.strip() for f in options('cluster.exec_groups').split(',')]
                     }
         }, options)    
    instances = getInstances(lambda i : i.publicDNS == options('general.name'))
    if not instances:
        raise MissingOptionError('Did not provide a valid host')

    mastInst = instances[0]

    ctype = ec2Control
    cl = Cluster(options('general.name'), ctype, conf)
    cl.setMaster(mastInst)
    cl.createExecs(options('general.num'), False)

    logPrint('The master IP is: ' + cl.master.publicDNS)

    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

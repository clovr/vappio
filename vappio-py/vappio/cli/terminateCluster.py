#!/usr/bin/env python

import os

from igs.utils.cli import MissingOptionError, buildConfigN, notNone, defaultIfNone
from igs.utils.config import configFromMap
from igs.utils.logging import logPrint

from igs.cgi.request import performQuery

from vappio.cluster.persist import load, dump, cleanup
from vappio.cluster.misc import getInstances
from vappio.cluster.control import terminateCluster

OPTIONS = [
    ('name', '', '--name', 'Name of cluster', notNone),
    ]


URL = '/vappio/clusterInfo_ws.py'

def main(options, _args):
    cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))

    ok, result = performQuery(cluster.master.publicDNS, URL, {})
    if not ok:
        raise Exception('I dunno...' + str(result))


    cluster.addExecNodes(getInstances(lambda i : i.publicDNS in result['execNodes'], cluster.ctype))
    cluster.addDataNodes(getInstances(lambda i : i.publicDNS in result['dataNodes'], cluster.ctype))

    terminateCluster(cluster)

    cleanup(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))
    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

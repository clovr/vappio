#!/usr/bin/env python
##
# Checks the status of all, or a specific pipeline, running on the cluster
import os

from igs.utils.cli import buildConfigN, MissingOptionError, notNone
from igs.utils.logging import logPrint, errorPrint
from igs.cgi.request import performQuery

from vappio.instance.control import runSystemInstanceEx

from vappio.cluster.persist import load, dump

OPTIONS = [
    ('name', '', '--name', 'Name of cluster', notNone),
    ]

URL = '/vappio/pipelineStatus_ws.py'

def main(options, args):
    cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))

    res = performQuery(cluster.master.publicDNS, URL, {'pipelines': args})
    keys = res.keys()
    keys.sort()
    print '%40s %10s %20s' % ('Name', 'Status', 'Type')
    print '\n'.join(['%40s %10s %20s' % (name, res[name][1]['state'], res[name][1]['ptype']) for name in keys])
        

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

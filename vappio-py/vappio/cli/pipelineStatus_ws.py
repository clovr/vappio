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

URL = '/vappio/pipelineStatus.py'



def main(options, args):
    cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))

    result = performQuery(cluster.master.publicDNS, URL, {'pipelines': args})
    try:
        ok, res = result
        if ok:
            print '\n'.join([name + ': ' + state[1] for name, state in res.iteritems()])
        else:
            print 'Failed: ' + res
    except:
        errorPrint('Unknown result: ' + data)

    

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

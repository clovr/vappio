#!/usr/bin/env python

import os

from igs.utils.cli import MissingOptionError, buildConfigN, notNone, defaultIfNone
from igs.utils.logging import logPrint, errorPrint
from igs.utils.functional import compose
from igs.cgi.request import performQuery

from vappio.cluster.persist import load, dump
from vappio.cluster.control import startExecNodes

OPTIONS = [
    ('name', '', '--name', 'Name of cluster (in this case public host name of master)', notNone),
    ('num', '', '--num', 'Number of nodes to create', compose(int, notNone)),
    ('update_dirs', '', '--update_dirs', 'Update scritps directories', defaultIfNone(False), True),
    ]

URL = '/vappio/addInstances.py'

def main(options, _args):
    cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))

    result = performQuery(cluster.master.publicDNS, URL, {'num': options('general.num'),
                                                          'update_dirs': options('general.update_dirs')})
    try:        
        ok, res = result
        if ok:
            logPrint('Launching %d instances' % options('general.num'))
        else:
            errorPrint('Failed: ' + str(res))
    except Exception, err:
        errorPrint('Failed: ' + str(err))
    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

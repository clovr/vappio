#!/usr/bin/env python
##
# Checks the status of a pipeline
import os
import httplib
import urllib
import json

from igs.utils.cli import buildConfigN, MissingOptionError, notNone

from igs.utils.logging import logPrint, errorPrint

from vappio.instance.control import runSystemInstanceEx

from vappio.cluster.persist import load, dump

OPTIONS = [
    ('name', '', '--name', 'Name of cluster', notNone),
    ]

URL = '/vappio/pipelineStatus.py'

def main(options, args):
    cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))
    params = urllib.urlencode({'pipeline': json.dumps(args)})
    conn = httplib.HTTPConnection(cluster.master.publicDNS)
    conn.request('POST', URL, params)
    data = conn.getresponse().read()
    try:
        ok, res = json.loads(data)
        if ok:
            print '\n'.join([name + ': ' + state for name, state in res.iteritems()])
        else:
            print 'Failed: ' + res
    except:
        errorPrint('Unknown result: ' + data)

    

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

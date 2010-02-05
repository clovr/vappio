#!/usr/bin/env python
##
# Runs a pipeline throuhg the webservice call
import os
import httplib
import urllib
import json

from igs.utils.cli import buildConfigN, MissingOptionError, notNone
from igs.utils.logging import logPrint, errorPrint
from igs.cgi.request import performQuery

from vappio.instance.control import runSystemInstanceEx

from vappio.cluster.persist import load, dump

OPTIONS = [
    ('name', '', '--name', 'Name of cluster', notNone),
    ('pipeline', '', '--pipeline', 'Type of pipeline', notNone),
    ('pipeline_name', '', '--pipeline-name', 'Name to give the pipeline', notNone)
    ]

URL = '/vappio/runPipeline.py'

def main(options, args):
    cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), options('general.name'))
    result = performQuery(cluster.master.publicDNS, URL, {'pipeline': options('general.pipeline'),
                                                          'pipeline_name': options('general.pipeline_name'),
                                                          'args': args
                                                          })
    try:
        ok, res = result
        if ok:
            logPrint('Pipeline Id: ' + str(res))
        else:
            errorPrint('Failed: ' + str(res))
    except:
        errorPrint('Unknown result: ' + str(result))

    

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS, usage='usage: %prog --name x --pipeline y [ -- options for pipeline]'))

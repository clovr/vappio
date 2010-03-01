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

from vappio.cluster.persist_mongo import load

OPTIONS = [
    ('name', '', '--name', 'Name of cluster', notNone),
    ('pipeline', '', '--pipeline', 'Type of pipeline', notNone),
    ('pipeline_name', '', '--pipeline-name', 'Name to give the pipeline', notNone)
    ]

URL = '/vappio/runPipeline_ws.py'

def main(options, args):
    cluster = load(options('general.name'))

    res = performQuery(cluster.master.publicDNS, URL, {'pipeline': options('general.pipeline'),
                                                       'pipeline_name': options('general.pipeline_name'),
                                                       'args': args
                                                       })
    logPrint('Pipeline Id: ' + str(res))

    

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS, usage='usage: %prog --name x --pipeline y [ -- options for pipeline]'))

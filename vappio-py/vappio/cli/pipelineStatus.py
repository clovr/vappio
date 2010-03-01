#!/usr/bin/env python
##
# Checks the status of all, or a specific pipeline, running on the cluster
import os

from igs.utils.cli import buildConfigN, notNone

from vappio.cluster.persist_mongo import load

from vappio.pipeline_tools.utils import pipelineStatus

OPTIONS = [
    ('name', '', '--name', 'Name of cluster', notNone),
    ]


def main(options, args):
    cluster = load(options('general.name'))

    ##
    # Return all those pipelines that match the lambda.  Either args is nothing in which
    # case return all or args contains a list of names so return only those pipelines in that
    # list of names
    pipelines = pipelineStatus(cluster, lambda p : not args or p['name'] in args)
    pipelines.sort(lambda p1, p2 : cmp(p1['name'], p2['name']))
    print '%40s %10s %20s %10s %10s' % ('Name', 'Status', 'Type', 'Complete', 'Total')
    print '\n'.join(['%40s %10s %20s %10d %10d' % (p['name'],
                                                   p['state'],
                                                   p['ptype'],
                                                   p['complete'],
                                                   p['total'])
                     for p in pipelines])
        

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

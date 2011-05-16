#!/usr/bin/env python
##
# Checks the status of all, or a specific pipeline, running on the cluster

from igs.utils import cli
from igs.utils import functional as func

from vappio.webservice import pipeline as pipeline_client

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', cli.defaultIfNone('localhost')),
    ('cluster', '', '--cluster', 'Name of cluster', cli.defaultIfNone('local')),
    ('pipeline_name', '-p', '--pipeline-name', 'Name of pipeline to show detauls on', func.identity)
    ]


def main(options, _args):
    if options('general.pipeline_name'):
        pipeline = pipeline_client.pipelineStatus(options('general.host'),
                                                  options('general.cluster'),
                                                  options('general.pipeline_name'))
        print 'PIPELINE_NAME\t%s' % pipeline['pipeline_name']
        print 'STATE\t%s' % pipeline['state']
        print 'CHILDREN\t%s' % ','.join([cl + ' ' + pName for cl, pName in pipeline['children']])
        print 'TASK\t%s' % pipeline['task_name']
        print 'CHECKSUM\t%s' % pipeline['checksum']
        print 'PROTOCOL\t%s' % pipeline['protocol']
        for i in pipeline['input_tags']:
            print 'INPUT_TAG\t%s' % i

        for i in pipeline['output_tags']:
            print 'OUTUPUT_TAG\t%s' % i

        keys = pipeline['config'].keys()
        keys.sort()
        for k in keys:
            print 'CONFIG\t%s\t%s' % (k, pipeline['config'][k])
    else:
        pipelines = pipeline_client.listPipelines(options('general.host'),
                                                  options('general.cluster'))

        for p in pipelines:
            print '\t'.join(['PIPELINE',
                             p['pipeline_name'],
                             p['state'],
                             p['task_name'],
                             p['protocol']])

if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))

#!/usr/bin/env python

from igs.utils import cli
from igs.utils import functional as func

from vappio.webservice import tag

from vappio.tasks.utils import runTaskStatus


OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', cli.defaultIfNone('localhost')),
    ('cluster',
     '',
     '--cluster',
     'Name of cluster to run this transfer on, --src-cluster and --dst-cluster must be in terms of this clusters perspective',
     cli.defaultIfNone('local')),
    ('tag_name', '', '--tag-name', 'Name of tag to upload', cli.notNone),
    ('src_cluster', '', '--src-cluster', 'Name of source cluster, hardcoded to local for now', cli.defaultIfNone('local')),
    ('dst_cluster', '', '--dst-cluster', 'Name of dest cluster', cli.defaultIfNone('local')),
    ('transfer_type', '', '--transfer-type', 'Type of transfer to do (cluster, s3) default is cluster',
     func.compose(cli.restrictValues(['cluster', 's3']), cli.defaultIfNone('cluster'))),
    ('block', '-b', '--block', 'Block until cluster is up (no longer used)', func.identity, cli.BINARY),
    ('compress', '', '--compress', 'Compress files', func.identity, cli.BINARY),
    ('compress_dir', '', '--compress-dir', 'Compress files into the specified directory', cli.defaultIfNone(None)),
    ('expand', '', '--expand', 'Expand files (always on regardless of this right now )', func.identity, cli.BINARY),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end', cli.defaultIfNone(False), cli.BINARY),
    ]


def transferBetweenClusters(options):
    return tag.transferTag(options('general.host'),
                           options('general.cluster'),
                           options('general.tag_name'),
                           options('general.src_cluster'),
                           options('general.dst_cluster'),
                           options('general.compress'),
                           options('general.compress_dir'))
                           

def transferToS3(options):
    pass
    
def main(options, _files):
    if options('general.transfer_type') == 'cluster':
        taskName = transferBetweenClusters(options)
    elif options('general.transfer_type') == 's3':
        if options('general.dst_cluster') != 'local':
            raise Exception('S3 is only for pushing to S3 from a cluster')
        taskName = transferToS3(options)
    else:
        raise Exception('Unknown transfer type: ' + options('general.transfer_type'))

    if options('general.print_task_name'):
        print taskName
    else:
        runTaskStatus(taskName)
    

if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))
    


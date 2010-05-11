#!/usr/bin/env python

from igs.utils.cli import buildConfigN, notNone, defaultIfNone, restrictValues

from vappio.core.error_handler import runCatchError, mongoFail
from vappio.webservice.cluster import loadCluster
from vappio.webservice.tag import tagData
from vappio.tags.transfer import downloadTag

OPTIONS = [
    ('tag_name', '', '--tag-name', 'Name of tag to transfer', notNone),
    ('src_cluster', '', '--src-cluster', 'Name of source cluster', notNone),
    ('dst_cluster', '', '--dst-cluster', 'Name of dest cluster, hardcoded to local for now', lambda _ : 'local'),
    ('expand', '', '--expand', 'Expand files', defaultIfNone(False), True)
    ]


def main(options, _args):
    srcCluster = loadCluster('localhost', options('general.src_cluster'))
    dstCluster = loadCluster('localhost', options('general.dst_cluster'))
    fileList = downloadTag(srcCluster, dstCluster, options('general.tag_name'))
    tagData('localhost',
            options('general.dst_cluster'),
            options('general.tag_name'),
            fileList,
            False,
            options('general.expand'),
            False,
            True)


if __name__ == '__main__':
    runCatchError(lambda : main(*buildConfigN(OPTIONS)),
                  mongoFail(dict(action='uploadTag')))

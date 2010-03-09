#!/usr/bin/env python

from igs.utils.cli import buildConfigN, notNone, defaultIfNone, restrictValues
from igs.utils.functional import identity

from vappio.core.error_handler import runCatchError, mongoFail
from vappio.webservice.cluster import loadCluster
from vappio.webservice.files import tagData
from vappio.tags.transfer import uploadTag

OPTIONS = [
    ('tag_name', '', '--tag-name', 'Name of tag to transfer', notNone),
    ('src_cluster', '', '--src-cluster', 'Name of source cluster, hardcoded to local for now', lambda _ : 'local'),
    ('dst_cluster', '', '--dst-cluster', 'Name of dest cluster', notNone),
    ('expand', '', '--expand', 'Expand files', defaultIfNone(False), True),
    ('tag_dir_base', '', '--tag-dir-base', 'Base directory in tags', identity)
    ]


def main(options, _args):
    srcCluster = loadCluster('localhost', options('general.src_cluster'))
    dstCluster = loadCluster('localhost', options('general.dst_cluster'))
    fileList = uploadTag(srcCluster, dstCluster, options('general.tag_name'), options('general.tag_dir_base'))
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

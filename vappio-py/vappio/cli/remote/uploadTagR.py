#!/usr/bin/env python
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone, restrictValues
from igs.utils.functional import identity
from igs.utils.ssh import scpToEx

from vappio.core.error_handler import runCatchError, mongoFail
from vappio.webservice.cluster import loadCluster
from vappio.webservice.files import tagData, realizePhantom
from vappio.tags.transfer import uploadTag
from vappio.tags.tagfile import loadTagFile, isPhantom

OPTIONS = [
    ('tag_name', '', '--tag-name', 'Name of tag to transfer', notNone),
    ('src_cluster', '', '--src-cluster', 'Name of source cluster, hardcoded to local for now', lambda _ : 'local'),
    ('dst_cluster', '', '--dst-cluster', 'Name of dest cluster', notNone),
    ('expand', '', '--expand', 'Expand files', defaultIfNone(False), True),
    ]


def main(options, _args):
    srcCluster = loadCluster('localhost', options('general.src_cluster'))
    dstCluster = loadCluster('localhost', options('general.dst_cluster'))
    tagFileName = os.path.join(srcCluster.config('dirs.tag_dir'), options('general.tag_name'))
    tagData = loadTagFile(tagFileName)

    if isPhantom(tagData):
        scpToEx(dstCluster.master.publicDNS,
                os.path.join(srcCluster.config('dirs.tag_dir'), options('general.tag_name') + '.phantom'),
                os.path.join(dstCluster.config('dirs.tag_dir'), options('general.tag_name') + '.phantom'),
                user=srcCluster.config('ssh.user'),
                options=srcCluster.config('ssh.options'),
                log=True)
        realizePhantom('localhost', dstCluster.name, options('general.tag_name'))
    else:
        ##
        # This should be fixed, right now there is a disconnect between what uploadTag
        # does in terms of where it places its data and then how tagData
        # should be called.  Perhaps these two calls should be placed into their
        # own call?
        # Perhaps uploadTag should return a tag and then tagData should take a tag
        # to be put on the remote box?  Not sure yet, leaning towards the latter
        fileList = uploadTag(srcCluster, dstCluster, tagData)
        tagData('localhost',
                options('general.dst_cluster'),
                options('general.tag_name'),
                os.path.join(dstCluster.config('dirs.tag_dir'), options('general.tag_name')),
                fileList,
                False,
                options('general.expand'),
                False,
                True)


if __name__ == '__main__':
    runCatchError(lambda : main(*buildConfigN(OPTIONS)),
                  mongoFail(dict(action='uploadTag')))

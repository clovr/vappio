#!/usr/bin/env python
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone, restrictValues
from igs.utils.functional import identity

from vappio.core.error_handler import runCatchError, mongoFail
from vappio.cluster.persist_mongo import load
from vappio.tags.tagfile import tagData


OPTIONS = [
    ('tag_name', '', '--tag-name', 'Name of the tag', identity),
    ('recursive', '', '--recursive', 'If file is a direcotry, recursively add files', defaultIfNone(False), True),
    ('expand', '', '--expand', 'If file is an archive (.bz2, .tar.gz, .tgz), expand it', defaultIfNone(False), True),
    ('append', '', '--append', 'Append files to the current file list, this will not add duplicates. The overwrite option supercedes this.', defaultIfNone(False), True),
    ('overwrite', '', '--overwrite', 'Overwrite tag if it already exists', defaultIfNone(False), True)
    ]


    

def main(options, files):
    cluster = load('local')
    if not options('general.tag_name'):
        raise Exception('Failed to provide a tag name')

    tagData(cluster.config('dirs.tag_dir'),
            options('general.tag_name'),
            files,
            recursive=options('general.recursive'),
            expand=options('general.expand'),
            append=options('general.append'),
            overwrite=options('general.overwrite'))


if __name__ == '__main__':
    runCatchError(lambda : main(*buildConfigN(OPTIONS)),
                  mongoFail(dict(action='tagData')))

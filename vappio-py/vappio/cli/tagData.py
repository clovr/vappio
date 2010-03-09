#!/usr/bin/env python
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.functional import identity

from vappio.webservice.files import tagData

OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', notNone),
    ('tag_name', '', '--tag-name', 'Name of tag', notNone),
    ('tag_base_dir', '', '--tag-base-dir', 'Base directory of the tag', identity),
    ('recursive', '-r', '--recursive', 'Recursively include directories', defaultIfNone(False), True),
    ('expand', '-e', '--expand', 'Expand archives', defaultIfNone(False), True),
    ('append', '-a', '--append', 'Append listed files to tag name, ignoring duplicate files', defaultIfNone(False), True),
    ('overwrite', '-o', '--overwrite', 'Overwrite file list if it exists', defaultIfNone(False), True)
    ]


def makeAbsolute(fname):
    """
    Makes a file name absolute by prepending the current working directory to it
    if it does not start with '/'
    """
    if fname[0] != '/':
        return os.path.join(os.getcwd(), fname)
    else:
        return fname

def main(options, files):
    tagData(options('general.host'),
            options('general.name'),
            options('general.tag_name'),
            options('general.tag_base_dir'),
            [makeAbsolute(f) for f in files],
            options('general.recursive'),
            options('general.expand'),
            options('general.append'),
            options('general.overwrite'))
    

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS, usage='--name=cluster --tag-name=name [options] file_1 .. file_n'))
    


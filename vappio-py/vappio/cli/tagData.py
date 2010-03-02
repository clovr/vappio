#!/usr/bin/env python

from igs.utils.cli import buildConfigN, notNone, defaultIfNone

from vappio.webservice.files import tagData

OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', notNone),
    ('tag_name', '', '--tag-name', 'Name of tag', notNone),
    ('recursive', '-r', '--recursive', 'Recursively include directories', defaultIfNone(False), True),
    ('expand', '-e', '--expand', 'Expand archives', defaultIfNone(False), True),
    ('append', '-a', '--append', 'Append listed files to tag name, ignoring duplicate files', defaultIfNone(True), True),
    ('overwrite', '-o', '--overwrite', 'Overwrite file list if it exists', defaultIfNone(True), True)
    ]

def main(options, files):
    tagData(options('general.host'),
            options('general.name'),
            options('general.tag_name'),
            files,
            options('general.recursive'),
            options('general.expand'),
            options('general.append'),
            options('general.overwrite'))
    

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS, usage='--name=cluster --tag-name=name [options] file_1 .. file_n'))
    


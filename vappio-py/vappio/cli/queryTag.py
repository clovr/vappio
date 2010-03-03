#!/usr/bin/env python

from igs.utils.cli import buildConfigN, notNone, defaultIfNone

from vappio.webservice.files import queryTag

OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', notNone),
    ('tag_name', '', '--tag-name', 'Name of tag', notNone),
    ]

def main(options, files):
    tagData = queryTag(options('general.host'),
                       options('general.name'),
                       options('general.tag_name'))
    for f in tagData('files'):
        print f
    

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))
    


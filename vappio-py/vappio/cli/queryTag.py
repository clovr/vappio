#!/usr/bin/env python

from igs.utils.cli import buildConfigN, notNone, defaultIfNone

from igs.utils import functional as func

from vappio.webservice import tag

OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', notNone),
    ('tag_name', '', '--tag-name', 'Name of tag', func.identity),
    ]

def main(options, files):
    if options('general.tag_name'):
        tagData = tag.queryTag(options('general.host'),
                               options('general.name'),
                               options('general.tag_name'))
        for f in tagData('files'):
            print '\t'.join(['FILE', f])

        metadataKeys = [k for k in tagData.keys() if k.startswith('metadata.')]
        for k in metadataKeys:
            print '\t'.join(['METADATA', '.'.join(k.split('.')[1:]), tagData(k)])
    else:
        tags = tag.listAllTags(options('general.host'), options('general.name'))
        for t in tags:
            print '\t'.join(['TAG', t])

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))
    


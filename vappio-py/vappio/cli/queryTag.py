#!/usr/bin/env python

from igs.utils import cli

from igs.utils import functional as func

from vappio.webservice import tag

OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', cli.defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', cli.defaultIfNone('local')),
    ('tag_name', '', '--tag-name', 'Name of tag', func.identity),
    ]

def main(options, files):
    if options('general.tag_name'):
        tagData = tag.queryTag(options('general.host'),
                               options('general.name'),
                               [options('general.tag_name')])
        if 'phantom_tag' in tagData:
            print 'PHANTOM'

        if 'files' in tagData:
            for f in tagData('files'):
                print '\t'.join(['FILE', f])

        metadataKeys = [k for k in tagData.keys() if k.startswith('metadata.')]
        for k in metadataKeys:
            print '\t'.join(['METADATA', '.'.join(k.split('.')[1:]), str(tagData(k))])
    else:
        tags = tag.listAllTags(options('general.host'), options('general.name'))
        for t in tags:
            print '\t'.join(['TAG', t])

if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))
    


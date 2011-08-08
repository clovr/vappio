#!/usr/bin/env python

from igs.utils import cli

from igs.utils import functional as func

from vappio.webservice import tag

OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', cli.defaultIfNone('localhost')),
    ('cluster', '', '--cluster', 'Name of cluster', cli.defaultIfNone('local')),
    ('tag_name', '', '--tag-name', 'Name of tag', func.identity),
    ]

def main(options, files):
    if options('general.tag_name'):
        tagData = tag.listTags(options('general.host'),
                               options('general.cluster'),
                               {'tag_name': options('general.tag_name')},
                               detail=True)[0]
        if tagData['phantom']:
            print 'PHANTOM'

        for f in tagData['files']:
            print '\t'.join(['FILE', f])

        for url in tagData['metadata'].get('urls', []):
            print '\t'.join(['URL', url])

        for k, v in tagData['metadata'].iteritems():
            if k not in ['urls']:
                print '\t'.join(['METADATA', k, str(v)])
    else:
        tags = tag.listTags(options('general.host'), options('general.cluster'), None, False)
        for t in tags:
            print '\t'.join(['TAG', t['tag_name'], str(t['file_count'])])

if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))
    


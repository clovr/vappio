#!/usr/bin/env python

from igs.utils.cli import buildConfigN, notNone, defaultIfNone

from vappio.webservice.files import uploadTag

OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', notNone),
    ('tag_name', '', '--tag-name', 'Name of tag to upload', notNone),
    ('src_cluster', '', '--src-cluster', 'Name of source cluster, hardcoded to local for now', lambda _ : 'local'),
    ('dst_cluster', '', '--dst-cluster', 'Name of dest cluster', notNone),
    ('expand', '', '--expand', 'Expand files', defaultIfNone(False), True)    
    ]

def main(options, files):
    uploadTag(options('general.host'),
              options('general.name'),
              options('general.tag_name'),
              options('general.src_cluster'),
              options('general.dst_cluster'),
              options('general.expand'))

    

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))
    


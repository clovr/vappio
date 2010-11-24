#! /usr/bin/env python
import sys
import os

from igs.utils import cli
from igs.utils import logging
from igs.utils import commands
from igs.utils import functional as func

#
# A bit unorthodoxed but it is useful that every CLI app
# is designed to also work as a library if needed
from vappio.cli import reliableDownloader

OPTIONS = [
    ('suffix', '-s', '--suffix',
     'The suffice that the md5 version of the files are expected to have.  Defaults to ".md5" (not the ".")', cli.defaultIfNone('.md5')),
    ('debug', '', '--debug', 'Add debug logging', func.identity, cli.BINARY)
    ]


def main(options, args):
    logging.DEBUG = options('general.debug')
    urls = []
    if not args:
        for line in [l for l in sys.stdin if l.strip()]:
            urls.append(line.strip() + options('general.suffix'))
    else:
        urls.extend([u + options('general.suffix') for u in args])

    for url in urls:
        reliableDownloader.deleteDownloadedFiles('/tmp', url)
        commands.runSystemEx(' '.join(['wget',
                                       '-P', '/tmp',
                                       '-nv',
                                       url]), log=logging.DEBUG)
        for f in reliableDownloader.getDownloadFilenames('/tmp', url):
            sys.stdout.write('\n'.join(['%s %s' % (l.strip().split()[0], os.path.join(os.path.dirname(url), l.strip().split()[1])) for l in open(f)]) + '\n')

        reliableDownloader.deleteDownloadedFiles('/tmp', url)
        

if __name__ == '__main__':
    sys.exit(main(*cli.buildConfigN(OPTIONS, usage='%prog [options] URLs')))

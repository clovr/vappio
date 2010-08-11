#!/usr/bin/env python
from igs.utils import cli

OPTIONS = [
    ]

def main(_options, args):
    host, ip = args
    for line in open('/etc/hosts'):
        sline = line.split()
        if host in sline:
            break
    else:
        # Not in there
        open('/etc/hosts', 'a').write('%s\t%s\t%s\n' % (ip, host, host))

if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))

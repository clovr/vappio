#!/usr/bin/env python
from igs.utils.cli import buildConfigN
from igs.utils.functional import identity


OPTIONS = [
    ('event', '', '--event', 'Event', identity),
    ('name', '', '--name', 'Name', identity),
    ('retval', '', '--retval', 'Retval', identity),
    ('time', '', '--time', 'Time', identity),
    ('file', '', '--file', 'File', identity),
    ('id', '', '--ID', 'ID', identity),
    ('props', '', '--props', 'Props', identity),
    ('host', '', '--host', 'Host', identity),
    ('message', '', '--message', 'Message', identity)
    ]


def main(options, _args):
    fout = open('/tmp/echo.log', 'a')
    if options('general.event') == 'finish' and ' workflow' in options('general.message'):
        fout.write('%s finished  %s %s\n' % (options('general.name'), options('general.file'), options('general.retval')))
        

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

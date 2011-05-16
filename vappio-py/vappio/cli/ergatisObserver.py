#!/usr/bin/env python
##
# This script observes a running pipeline and feeds updates back to the associated task
from igs.utils import cli
from igs.utils import functional as func

from igs.cgi import request

OPTIONS = [
    ('event', '', '--event', 'Event', func.identity),
    ('name', '', '--name', 'Name', func.identity),
    ('retval', '', '--retval', 'Retval', func.identity),
    ('time', '', '--time', 'Time', func.identity),
    ('file', '', '--file', 'File', func.identity),
    ('id', '', '--ID', 'ID', func.identity),
    ('props', '', '--props', 'Props', func.identity),
    ('host', '', '--host', 'Host', func.identity),
    ('message', '', '--message', 'Message', func.identity)
    ]


def main(options, _args):
    try:
        d = dict((k, options(k))
                 for k in ['event',
                           'name',
                           'retval',
                           'time',
                           'file',
                           'id',
                           'props',
                           'host',
                           'message'])
        request.performQuery('localhost',
                             '/vappio/observer_ws.py',
                             d)
    except Exception, err:
        open('/tmp/ergatisObserver.log', 'a').write(str(err) + '\n')

if __name__ == '__main__':
    try:
        main(*cli.buildConfigN(OPTIONS, putInGeneral=False))
    except Exception, err:
        open('/tmp/ergatisObserver.log', 'a').write(str(err) + '\n')

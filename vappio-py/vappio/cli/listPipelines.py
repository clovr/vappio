#!/usr/bin/env python
##
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.functional import compose

OPTIONS = [
    ('vappio_home', '', '--vappio_home', 'Location of vappio scripts, defaults to $VAPPIO_HOME', compose(notNone, defaultIfNone(os.getenv('VAPPIO_HOME')))),
    ]


def main(options, _args):
    pipelines = [f[:-3]
                 for f in os.listdir(os.path.join(options('general.vappio_home'),
                                                  'vappio-py',
                                                  'vappio',
                                                  'pipelines'))
                 if f.endswith('.py') and f != '__init__.py']
    print 'Available pipelines:'
    print '\n'.join(['\t' + f for f in pipelines])


if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

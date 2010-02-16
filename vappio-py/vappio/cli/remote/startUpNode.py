#!/usr/bin/env python
##
# This runs when a node comes up in order to start it
from vappio.instance.startup import startUpFromConfigFile


def main(options):
    startUpFromConfigFile('/tmp/machine.conf')


if __name__ == '__main__':
    main(None)
    

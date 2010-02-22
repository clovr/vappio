#!/usr/bin/env python
##
# This runs when a node comes up in order to start it
from vappio.instance.shutdown import shutdownFromConfigFile


def main(options):
    shutdownFromConfigFile('/tmp/machine.conf')


if __name__ == '__main__':
    main(None)
    

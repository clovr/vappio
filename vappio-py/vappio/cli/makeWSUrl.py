#!/usr/bin/env python
##
# This is a simple program to make web service call URLs and even do the call
import sys
import json

from igs.utils import cli #import buildConfigN, notNone, defaultIfNone, restrictValues
from igs.utils import functional as func

OPTIONS = [
    ('json', '-j', '--json', 'JSON to pass (reads from stdin by default)', func.identity),
    ('do_request', '-d', '--do', 'Do the actual request and print the results rather than just the URL', func.identity),
    ('url', '-u', '--url', 'URL to perform the query on', cli.notNone),
    ]



def main(options, _args):
    pass

if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))
    

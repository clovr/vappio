#!/usr/bin/env python
##
# This is a simple program to make web service call URLs and even do the call
import sys
import json
from urlparse import urlparse

from igs.utils import cli
from igs.utils import functional as func

from igs.cgi import request

OPTIONS = [
    ('json', '-j', '--json', 'JSON to pass (reads from stdin by default)', func.identity),
    ('do_request', '-d', '--do', 'Do the actual request and print the results rather than just the URL', func.identity, True),
    ('url', '-u', '--url', 'URL to perform the query on', cli.notNone),
    ]



def main(options, _args):
    if options('general.json'):
        jsonQuery = options('general.json')
    else:
        jsonQuery = sys.stdin.read()


    urlParsed = urlparse(options('general.url'))
        
    if options('general.do_request'):
        print json.dumps(request.performQuery(urlParsed.netloc, urlparsed.path, json.loads(jsonQuery)))
        
if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))
    

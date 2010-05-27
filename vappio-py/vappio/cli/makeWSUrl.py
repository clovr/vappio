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
    ('url', '-u', '--url', 'URL to perform the query on', cli.notNone),
    ('debug', '-d', '--debug', 'Turn debugging on so you can see exactly what is going on behind the scenes', func.identity, True)
    ]



def main(options, _args):
    if options('general.json'):
        jsonQuery = options('general.json')
    else:
        jsonQuery = sys.stdin.read()


    urlParsed = urlparse(options('general.url'))
        
    print json.dumps(request.performQuery(urlParsed.netloc, urlParsed.path, json.loads(jsonQuery), debug=options('general.debug')), indent=True)
        
if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))
    

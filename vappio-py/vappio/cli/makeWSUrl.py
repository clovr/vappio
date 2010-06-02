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
    ('debug', '-d', '--debug', 'Turn debugging on so you can see exactly what is going on behind the scenes', func.identity, True)
    ]



def main(options, args):
    if options('general.json'):
        jsonQuery = options('general.json')
    else:
        jsonQuery = sys.stdin.read()


    if not args:
        raise Exception('You must specify a URL')
    else:
        url = args[0]
        
    urlParsed = urlparse(url)

    
    print json.dumps(json.loads(request.performQueryNoParse(urlParsed.netloc, urlParsed.path, json.loads(jsonQuery), debug=options('general.debug'))), indent=True)
        
if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))
    

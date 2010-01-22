#!/usr/bin/env python

import cgi

from igs.cgi.handler import CGIPage, generatePage


class Page(CGIPage):

    def body(self):
        return '<html><head><title>testing</title></head><body>Hi</body></html>'


generatePage(Page())

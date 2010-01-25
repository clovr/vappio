#!/usr/bin/env python

import cgi
import json

from igs.utils.core import getStrBetween

from igs.cgi.handler import CGIPage, generatePage


def getPipelineStatus(pipeline):
    for line in open('/mnt/projects/clovr/workflow/runtime/pipeline/%s/pipeline.xml' % pipeline):
        if '<state>' in line:
            return getStrBetween(line, '<state>', '</state>')

    return 'Unknown'

class PipelineStatus(CGIPage):

    def body(self):
        form = cgi.FieldStorage()
        pipelines = form.getlist('pipeline')

        ##
        # No pipelines means return empty
        if not pipelines:
            return json.dumps({})
        else:
            ret = {}
            for p in pipelines:
                ret[p] = getPipelineStatus(p)

            return json.dumps(ret)

generatePage(PipelineStatus())

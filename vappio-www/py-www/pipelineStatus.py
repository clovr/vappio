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
        pipelines = form.getlist('pipeline_id')

        ##
        # No pipelines means return empty
        return json.dumps(dict([(p, getPipelineStatus(p)) for p in pipelines]))

generatePage(PipelineStatus())

#!/usr/bin/env python
##
import os
import json

from twisted.python import reflect

from igs.cgi.handler import CGIPage, generatePage
from igs.cgi.request import readQuery

from igs.utils import config


def loadConfig(conf, pipeline):
    pModule = reflect.namedAny('vappio.pipelines.' + pipeline)
    ##
    # This is temporary until all of the pipelines support this config template
    try:
        pConf = config.configFromStream(open(os.path.join(conf('dirs.clovr_pipelines_template_dir'),
                                                          pModule.TEMPLATE_NAME,
                                                          pModule.TEMPLATE_NAME + '.config.tmpl')),
                                        lazy=True)
        return dict([(k, json.loads(v)) for k, v in config.configToDict(pConf).iteritems()])
    except IOError:
        return None
        

class ListPipelines(CGIPage):
    def body(self):
        conf = config.configFromStream(open('/tmp/machine.conf'), base=config.configFromEnv())
        pipelines = [f[:-3]
                     for f in os.listdir(os.path.join(conf('env.VAPPIO_HOME'),
                                                      'vappio-py',
                                                      'vappio',
                                                      'pipelines'))
                     if f.endswith('.py') and f != '__init__.py']
        
        pipelineData = [dict(name=p,
                             config=loadConfig(conf, p))
                        for p in pipelines]

        return pipelineData
               

        
generatePage(ListPipelines())


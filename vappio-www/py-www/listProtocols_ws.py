#!/usr/bin/env python
##
import os
import json

from twisted.python import reflect

from igs.cgi.handler import CGIPage, generatePage

from igs.utils import config

class JSONParseError(Exception):
    def __init__(self, value):
        self.value = value

class PipelineTmplParseError(Exception):
    def __init__(self, pipeline, value):
        self.pipeline = pipeline
        self.value = value

    def __str__(self):
        return 'Error parsing %s line: %s' % (self.pipeline, self.value)
        
def jsonLoads(v):
    try:
        return json.loads(v)
    except:
        open('/tmp/listProtocols.log', 'a').write(v + '\n')
        raise JSONParseError(v)

def loadConfig(conf, pipeline):
    pModule = reflect.namedAny('vappio.pipelines.' + pipeline)
    try:
        pConf = config.configListFromStream(open(os.path.join(conf('dirs.clovr_pipelines_template_dir'),
                                                              pModule.TEMPLATE_NAME,
                                                              pModule.TEMPLATE_NAME + '.config.tmpl')))
        
        return [(k, jsonLoads(v)) for k, v in pConf]
    except IOError:
        return None
    except JSONParseError, err:
        raise PipelineTmplParseError(pipeline, err.value)
        

class ListProtocols(CGIPage):
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
               

        
generatePage(ListProtocols())


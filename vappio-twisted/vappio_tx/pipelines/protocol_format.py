#
# Handles the protocol format
import os
import json

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
        raise JSONParseError(v)
        
def load(conf, protocol):
    """
    Load the protocol and return a list of keys and jsons
    """
    try:
        pConf = config.configListFromStream(open(os.path.join(conf('dirs.clovr_pipelines_template_dir'),
                                                              protocol,
                                                              protocol + '.config.tmpl')))
        return [(k, jsonLoads(v)) for k, v in pConf]
    except JSONParseError, err:
        raise PipelineTmplParseError(protocol, err.value)    


def protocols(conf):
    """
    List all protocols
    """
    protocolDir = conf('dirs.clovr_pipelines_template_dir')
    possibleProtocols = os.listdir(protocolDir)

    return [protocol
            for protocol in possibleProtocols
            if os.path.exists(os.path.join(protocolDir, protocol, protocol + '.config.tmpl'))]


    
def applyProtocol(protocolConf, pipelineConf):
    """
    `protocolConf` is the result of a `load`, `pipelineConf` is the
    filled out protocol configuration.  This takes a pipeline configuration
    and applies any invariants from the protocol configuration.

    This currently just consists of `always_hidden` elements
    """
    for k, v in protocolConf:
        if v.get('visibility') == 'always_hidden':
            pipelineConf[k] = v.get('default', '')

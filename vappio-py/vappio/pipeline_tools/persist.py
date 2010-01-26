##
# Tools for persisting pipeline data to disk
import os
import json

from twisted.python.reflect import fullyQualifiedName, namedAny

from igs.utils.config import configFromMap
from igs.utils.commands import runSystemEx

from vappio.ergatis.pipeline import Pipeline

class PipelineDoesNotExist(Exception):
    pass


def writeFile(fname, data):
    fout = open(fname, 'w')
    fout.write(data)
    fout.close()


def dump(baseDir, pipeline):
    """
    Dumps pipeline info to a directory structure
    """
    pipelineDir = os.path.join(baseDir, 'db', 'pipeline', pipeline.name)
    if not os.path.exists(pipelineDir):
        runSystemEx('mkdir -p ' + pipelineDir)


    writeFile(os.path.join(pipelineDir, 'ptype'), pipeline.ptype)
    writeFile(os.path.join(pipelineDir, 'pid'), pipeline.pid)
    ##
    # let's let json serialize this for us
    writeFile(os.path.join(pipelineDir, 'conf'), json.dumps(dict([(k, pipeline.config(k)) for k in pipeline.config.keys()])))

def load(baseDir, name):
    """
    Loads a pipeline by name and returns a Pipeline object
    """
    pipelineDir = os.path.join(baseDir, 'db', 'pipeline', name)
    if not os.path.exists(pipelineDir):
        raise PipelineDoesNotExist('Could not find pipeline: ' + name)

    ptype = open(os.path.join(pipelineDir, 'ptype')).read().strip()
    pid = open(os.path.join(pipelineDir, 'pid')).read().strip()
    conf = configFromMap(json.loads(open(os.path.join(pipelineDir, 'conf')).read()))

    return Pipeline(name, pid, ptype, conf)

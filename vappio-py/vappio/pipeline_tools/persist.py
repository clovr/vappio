##
# Tools for persisting pipeline data to MongoDB
import os
import json

import pymongo

from twisted.python.reflect import fullyQualifiedName, namedAny

from igs.utils.config import configFromMap
from igs.utils.commands import runSystemEx

from vappio.ergatis.pipeline import Pipeline


class PipelineDoesNotExist(Exception):
    pass


def dump(baseDir, pipeline):
    """
    Dumps pipeline info to mongodb, baseDir will be removed in future
    """
    pipelines = pymongo.Connection().clovr.pipelines

    pipelines.insert(dict(_id=pipeline.name,
                          name=pipeline.name,
                          ptype=fullyQualifiedName(pipeline.ptype),
                          pid=pipeline.pid))
                          conf=dict([(k.replace('.', '|'), pipeline.config(k)) for k in pipeline.config.keys()])))
    
def load(baseDir, name):
    """
    Loads a pipeline by name, returning a Pipeline.  baseDir will be removed soon
    """
    pipelines = pymongo.Connection().clovr.pipelines
    pipeline = pipelines.find_one({'name': name})
    if pipeline is None:
        raise PipelineDoesNotExist('Could not find pipeline: ' + name)

    ptype = namedAny(pipeline['ptype'])
    pid = pipeline['pid']
    conf = configFromMap([(k.replace('|', '.'), v) for k, v in pipeline['conf'].iteritems()])
    
    return Pipeline(name, pid, ptype, conf)
    


def loadAll(baseDir):
    """
    Loads all of the pipelines
    """
    pipelines = pymongo.Connection().clovr.pipelines
    return [load(baseDir, p['name']) for p in pipelines.find()]

    

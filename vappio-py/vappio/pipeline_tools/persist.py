##
# Tools for persisting pipeline data to MongoDB
import json

import pymongo

from twisted.python.reflect import fullyQualifiedName, namedAny

from igs.utils.config import configFromMap

from vappio.ergatis.pipeline import Pipeline


class PipelineDoesNotExist(Exception):
    pass


def dump(pipeline):
    """
    Dumps pipeline info to mongodb
    """
    pipelines = pymongo.Connection().clovr.pipelines

    pipelines.insert(dict(_id=pipeline.name,
                          name=pipeline.name,
                          taskName=pipeline.taskName,
                          ptype=fullyQualifiedName(pipeline.ptype),
                          pid=pipeline.pid,
                          conf=json.dumps(dict([(k, pipeline.config(k)) for k in pipeline.config.keys()]))))
    
def load(name):
    """
    Loads a pipeline by name, returning a Pipeline.
    """
    pipelines = pymongo.Connection().clovr.pipelines
    pipeline = pipelines.find_one({'name': name})
    if pipeline is None:
        raise PipelineDoesNotExist('Could not find pipeline: ' + name)

    taskName = pipeline['taskName']
    ptype = namedAny(pipeline['ptype'])
    pid = pipeline['pid']
    conf = configFromMap(json.loads(pipeline['conf']))
    
    return Pipeline(name, taskName, pid, ptype, conf)
    


def loadAll():
    """
    Loads all of the pipelines
    """
    pipelines = pymongo.Connection().clovr.pipelines
    return [load(p['name']) for p in pipelines.find()]

    

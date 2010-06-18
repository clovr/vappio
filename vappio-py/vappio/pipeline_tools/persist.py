##
# Tools for persisting pipeline data to MongoDB
import json

import pymongo

from twisted.python.reflect import fullyQualifiedName, namedAny

from igs.utils import functional as func

class PipelineDoesNotExist(Exception):
    pass


def dump(pipeline):
    """
    Dumps pipeline info to mongodb
    """
    pipelines = pymongo.Connection().clovr.pipelines
    pipelines.insert(func.updateDict(dict(_id=pipeline['name']), pipeline))
    
def load(name):
    """
    Loads a pipeline by name, returning a Pipeline.
    """
    pipelines = pymongo.Connection().clovr.pipelines
    pipeline = pipelines.find_one({'name': name})
    if pipeline is None:
        raise PipelineDoesNotExist('Could not find pipeline: ' + name)

    return pipeline


def loadAll():
    """
    Loads all of the pipelines
    """
    pipelines = pymongo.Connection().clovr.pipelines
    return [load(p['name']) for p in pipelines.find()]

    

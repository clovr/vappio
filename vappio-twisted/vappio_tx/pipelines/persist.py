import json

import pymongo

from twisted.internet import threads

from igs.utils import functional as func
from igs.utils import config as config_

from vappio.tasks import task

class PipelineNotFoundError(Exception):
    pass

class Pipeline(func.Record):
    IDLE = task.TASK_IDLE
    RUNNING = task.TASK_RUNNING
    COMPLETED = task.TASK_COMPLETED
    FAILED = task.TASK_FAILED
    
    def __init__(self,
                 pipelineId,
                 pipelineName,
                 userName,
                 protocol,
                 checksum,
                 taskName,
                 queue,
                 children,
                 config):
        func.Record.__init__(self,
                             pipelineId=pipelineId,
                             pipelineName=pipelineName,
                             userName=userName,
                             protocol=protocol,
                             checksum=checksum,
                             taskName=taskName,
                             queue=queue,
                             children=children,
                             config=config_.configFromMap(config, lazy=True))

def _documentToPipeline(doc):
    conf = json.loads(doc['config'])
    return Pipeline(pipelineId=doc['pipeline_id'],
                    pipelineName=doc['pipeline_name'],
                    userName=doc['user_name'],
                    protocol=doc['protocol'],
                    checksum=doc['checksum'],
                    taskName=doc['task_name'],
                    queue=doc['queue'],
                    children=doc['children'],
                    config=conf)

def _documentFromPipeline(p):
    jsonConf = json.dumps(config_.configToDict(p.config))
    return {'pipeline_id': p.pipelineId,
            'pipeline_name': p.pipelineName,
            'user_name': p.userName,
            'protocol': p.protocol,
            'checksum': p.checksum,
            'task_name': p.taskName,
            'queue': p.queue,
            'children': p.children,
            'config': jsonConf}

def pipelineToDict(p):
    return {'pipeline_id': p.pipelineId,
            'pipeline_name': p.pipelineName,
            'user_name': p.userName,
            'protocol': p.protocol,
            'checksum': p.checksum,
            'task_name': p.taskName,
            'queue': p.queue,
            'children': p.children,
            'config': config_.configToDict(p.config)}

def pipelineFromDict(d):
    return Pipeline(pipelineId=d['pipeline_id'],
                    pipelineName=d['pipeline_name'],
                    userName=d['user_name'],
                    protocol=d['protocol'],
                    checksum=d['checksum'],
                    taskName=d['task_name'],
                    queue=d['queue'],
                    children=d['children'],
                    config=config_.configFromMap(d['config'], lazy=True))

def loadAllPipelinesByAdmin(criteria):
    def _query():
        conn = pymongo.Connection()
        return conn.clovr.pipelines.find(criteria)

    def _convertToPipeline(r):
        return [_documentToPipeline(p) for p in r]
    
    d = threads.deferToThread(_query)
    d.addCallback(_convertToPipeline)
    return d    

def loadAllPipelinesBy(criteria, userName):
    """
    Loads all pipelines that match the the provided criteria and returns a list
    of them.
    """
    return loadAllPipelinesByAdmin(func.updateDict(criteria, {'user_name': userName}))

def loadPipelineBy(criteria, userName):
    """
    Loads any pipelines that correspond to a criteria and returns the first
    one in the list of responses.  Throws PipelineNotFoundError if no pipeline
    is found.
    """
    def _checkForEmptyResponse(r):
        if not r:
            raise PipelineNotFoundError(criteria)
        return r

    d = loadAllPipelinesBy(criteria, userName)
    d.addCallback(_checkForEmptyResponse)
    d.addCallback(lambda r : r[0])
    return d


def savePipeline(pipeline):
    def _save():
        conn = pymongo.Connection()
        conn.clovr.pipelines.save(func.updateDict({'_id': pipeline.pipelineName},
                                                  _documentFromPipeline(pipeline)), safe=True)
        return pipeline

    return threads.deferToThread(_save)

from twisted.internet import defer

from igs.utils import config

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.pipelines import persist
from vappio_tx.pipelines import pipeline_misc

from vappio_tx.tasks import tasks

class Error(Exception):
    pass


@defer.inlineCallbacks
def handleWWWPipelineCreate(request):
    """
    Sets the config section of a pipeline exactly to what is given
    Input:
    { cluster: string
      user_name: string
      pipeline_name : string
      protocol : string
      queue : string
      config: { key/value }
      ?pipeline_id : string
      ?task_name : string
      ?pipeline_parent : pipeline_name
    }

    Output:
    Pipeline
    """

    if request.body.get('parent_pipeline'):
        parentPipelines = yield request.state.pipelinePersist.loadAllPipelinesBy({'pipeline_name': request.body['parent_pipeline']},
                                                                                 request.body['user_name'])
        if len(parentPipelines) == 1:
            parentPipeline = parentPipelines[0]
        else:
            raise Exception('More than one possible parent pipeline choice, not sure what to do here')        
    else:
        parentPipeline = None
    
    if 'task_name' in request.body:
        taskName = request.body['task_name']
    else:
        taskName = yield tasks.createTaskAndSave('runPipelines', 0)

        
    pipeline = persist.Pipeline(pipelineId=request.body.get('pipeline_id', None),
                                pipelineName=request.body['pipeline_name'],
                                userName=request.body['user_name'],
                                protocol=request.body['protocol'],
                                checksum=pipeline_misc.checksumInput(request.body['config']),
                                taskName=taskName,
                                queue=request.body['queue'],
                                children=[],
                                config=request.body['config'])

    yield request.state.pipelinePersist.savePipeline(pipeline)
    pipelineDict = yield request.state.pipelinesCache.pipelineToDict(pipeline)


    if parentPipeline:
        childPipeline = [('local',
                          request.body['pipeline_name'])]
        parentPipeline = parentPipeline.update(children=list(set([tuple(e)
                                                                  for e in parentPipeline.children + childPipeline])))
        yield request.state.pipelinePersist.savePipeline(parentPipeline)
        
    defer.returnValue(request.update(response=pipelineDict))

def subscribe(mq, state):
    processPipelineCreate = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                    'user_name',
                                                                                    'pipeline_name',
                                                                                    'protocol',
                                                                                    'queue',
                                                                                    'config']),
                                                                  pipeline_misc.forwardToCluster(state.conf,
                                                                                                 state.conf('pipelines.create_www')),
                                                                  handleWWWPipelineCreate]))
    queue.subscribe(mq,
                    state.conf('pipelines.create_www'),
                    state.conf('pipelines.concurrent_create'),
                    queue.wrapRequestHandler(state, processPipelineCreate))

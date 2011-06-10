import os

from twisted.internet import defer
from twisted.internet import reactor

from igs.utils import config
from igs.utils import functional as func

from igs_tx.utils import defer_utils
from igs_tx.utils import defer_pipe

from vappio_tx.www_client import pipelines as pipelines_www_client
from vappio_tx.www_client import tags as www_tags

from vappio_tx.utils import queue
from vappio_tx.utils import mongo_cache

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.pipelines import persist
from vappio_tx.pipelines import pipeline_monitor
from vappio_tx.pipelines import protocol_format

PIPELINES_UPDATE_FREQUENCY = 30

@defer.inlineCallbacks
def pipelineToDict(machineConf, p):
    protocolConf = protocol_format.load(machineConf, p.config('pipeline.PIPELINE_TEMPLATE'))

    inputTagsList = [p.config(k).split(',')
                     for k, v in protocolConf
                     if v.get('type').split()[0] in ['dataset',
                                                     'blastdb_dataset',
                                                     'paired_dataset',
                                                     'singleton_dataset'] and p.config(k)]
    inputTags = []
    for i in inputTagsList:
        inputTags.extend(i)


    possibleOutputTags = set([p.pipelineName + '_' + t.strip()
                              for t in p.config('output.TAGS_TO_DOWNLOAD', default='').split(',')])

    query = [{'tag_name': t} for t in possibleOutputTags]
    
    tags = yield www_tags.loadTagsBy('localhost', 'local', p.userName, {'$or': query}, False)

    tags = set([t['tag_name'] for t in tags])

    outputTags = list(tags & possibleOutputTags)
    
    pipelineTask = yield tasks_tx.loadTask(p.taskName)
    
    defer.returnValue({'pipeline_id': p.pipelineId,
                       'pipeline_name': p.pipelineName,
                       'user_name': p.userName,
                       'wrapper': p.protocol == 'clovr_wrapper',
                       'protocol': p.config('pipeline.PIPELINE_TEMPLATE'),
                       'checksum': p.checksum,
                       'task_name': p.taskName,
                       'queue': p.queue,
                       'children': p.children,
                       'state': pipelineTask.state,
                       'num_steps': pipelineTask.numTasks,
                       'num_complete': pipelineTask.completedTasks,
                       'input_tags': inputTags,
                       'output_tags': outputTags,
                       'pipeline_desc': p.config('pipeline.PIPELINE_DESC', default=''),
                       'config': config.configToDict(p.config),
                       })

def removeDetail(p):
    p = dict(p)
    p.pop('config')
    return p

@defer.inlineCallbacks
def pipelineToDictLite(machineConf, p):
    pipelineDict = yield pipelineToDict(machineConf, p)
    defer.returnValue(removeDetail(pipelineDict))


@defer.inlineCallbacks
def handleWWWPipelineList(request):
    """
    Input:
    { cluster: string
      user_name: string
      ?criteria: { key/value }
      ?detail: boolean
    }
    Output:
    pipeline
    """
    pipelinesDict = yield request.state.pipelinesCache.query(func.updateDict({'user_name': request.body['user_name']},
                                                                             request.body.get('criteria', {})))

    if not request.body.get('detail', False):
        pipelinesDict = map(removeDetail, pipelinesDict)
    
    defer.returnValue(request.update(response=pipelinesDict))


@defer.inlineCallbacks
def _cachePipelines(state):
    pipelines = yield persist.loadAllPipelinesByAdmin({})
    pipelinesDict = yield defer_utils.mapSerial(lambda p : pipelineToDict(state.machineconf, p),
                                                pipelines)

    yield defer_utils.mapSerial(state.pipelinesCache.save, pipelinesDict)
    reactor.callLater(PIPELINES_UPDATE_FREQUENCY, _cachePipelines, state)

@defer.inlineCallbacks
def _monitorAnyPipelines(mq, state):
    @defer.inlineCallbacks
    def _loadPipeline(p):
        pl = yield pipelineToDictLite(state.machineconf, p)
        defer.returnValue((p, pl))


    state.pipelinesCache = yield mongo_cache.createCache('pipelines_cache',
                                                         lambda d : func.updateDict(d, {'_id': d['pipeline_name']}))
    yield _cachePipelines(state)
    
    pipelines = yield persist.loadAllPipelinesByAdmin({})

    # Expand out so we have state information
    pipelinesLite = yield defer_utils.mapSerial(_loadPipeline, pipelines)

    pipelines = [p
                 for p, pl in pipelinesLite
                 if pl['state'] not in [tasks_tx.task.TASK_COMPLETED,
                                        tasks_tx.task.TASK_FAILED]]
    
    for p in pipelines:
        pipeline_monitor.monitor(pipeline_monitor.MonitorState(state.conf,
                                                               state.machineconf,
                                                               mq,
                                                               p))

    

def _forwardToCluster(conf, queueUrl):
    return queue.forwardRequestToCluster(conf('www.url_prefix') + '/' + os.path.basename(queueUrl))


@defer.inlineCallbacks
def subscribe(mq, state):
    yield _monitorAnyPipelines(mq, state)
    processPipelineList = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                  'user_name']),
                                                                _forwardToCluster(state.conf, state.conf('pipelines.list_www')),
                                                                handleWWWPipelineList]))
    queue.subscribe(mq,
                    state.conf('pipelines.list_www'),
                    state.conf('pipelines.concurrent_list'),
                    queue.wrapRequestHandler(state, processPipelineList))


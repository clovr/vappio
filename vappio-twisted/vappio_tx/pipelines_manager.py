# Common types:
# lite_pipeline:
# { pipeline_name: string
#   protocol: string
#   checksum: string
#   task_name: string
#   state: string
#   num_steps: int
#   num_complete: int
#   input_tags: [string]
#   output_tags: [string]
# }
import os
import hashlib
import json

from twisted.python import log

from twisted.internet import defer

from igs.utils import config
from igs.utils import functional as func

from igs_tx.utils import defer_utils
from igs_tx.utils import defer_pipe

from vappio_tx.internal_client import clusters as clusters_client

from vappio_tx.www_client import pipelines as pipelines_www_client

from vappio_tx.utils import queue

from vappio_tx.mq import client

from vappio_tx.pipelines import persist

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.pipelines import protocol_format
from vappio_tx.pipelines import pipeline_validate
from vappio_tx.pipelines import pipeline_run
from vappio_tx.pipelines import pipeline_monitor

class InvalidPipelineConfig(Exception):
    pass

class InvalidParentPipeline(Exception):
    def __init__(self, parentName):
        self.parentName = parentName

    def __str__(self):
        return 'Unknown parent pipeline: ' + self.parentName

class State:
    def __init__(self, conf):
        self.conf = conf
        self.machineconf = config.configFromStream(open(conf('config.machine_conf')),
                                                   base=config.configFromEnv())

def _containsPipelineTemplate(request):
    if 'pipeline.PIPELINE_TEMPLATE' in request.body['config']:
        return defer_pipe.ret(request)
    else:
        raise Exception('Must provide a config with pipeline.PIPELINE_TEMPLATE')

def _validatePipelineConfig(request):
    validateState = func.Record(conf=request.state.conf,
                                machineconf=request.state.machineconf,
                                mq=request.mq)
    protocolConf = protocol_format.load(request.state.machineconf,
                                        request.body['config']['pipeline.PIPELINE_TEMPLATE'])

    if not request.body['bare_run']:
        protocolConf += protocol_format.load(request.state.machineconf,
                                             'clovr_wrapper')
        
    protocol_format.applyProtocol(protocolConf, request.body['config'])
    return pipeline_validate.validate(validateState, protocolConf, request.body['config'])    


def _checksumInput(request):
    keys = [k for k in request.body['config'].keys() if k.startswith('input.') or k.startswith('params.')]
    keys.sort()

    valuesCombined = ','.join([request.body['config'][k] for k in keys])

    return hashlib.md5(valuesCombined).hexdigest()

@defer.inlineCallbacks
def _pipelineToDictLite(machineConf, p):
    protocolConf = protocol_format.load(machineConf, p.config('pipeline.PIPELINE_TEMPLATE'))

    inputTags = [p.config(k)
                 for k, v in protocolConf
                 if v.get('type') in ['dataset', 'blast_db_dataset']]
    outputTags = []

    pipelineTask = yield tasks_tx.loadTask(p.taskName)
    
    defer.returnValue({'pipeline_id': p.pipelineId,
                       'pipeline_name': p.pipelineName,
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
                       'pipeline_desc': p.config('pipeline.PIPELINE_DESC', default='')
                       })

def _deepValidation(request, pipeline):
    # Add stuff here
    return defer.succeed(pipeline)

def _runPipeline(request, pipeline):
    runState = func.Record(conf=request.state.conf,
                           machineconf=request.state.machineconf,
                           mq=request.mq)
    return pipeline_run.run(runState, pipeline)

def _monitor(request, pipeline):
    monitorState = pipeline_monitor.MonitorState(request.state.conf,
                                                 request.state.machineconf,
                                                 request.mq,
                                                 pipeline)
    return pipeline_monitor.monitor(monitorState)


@defer.inlineCallbacks
def handleWWWRunPipeline(request):
    """
    In the case of a pipeline we will do all the work necessary to
    run the pipeline and then setup a listener to run in the background
    tracking its progress.

    If bare_run is False then the pipeline run will actually be wrapped in
    `clovr_wrapper`.  Otherwise a pipeline of the type pipeline.PIPELINE_TEMPLATE
    is run.
    
    Input:
    { cluster: string
      user_name: string
      ?parent_pipeline: string
      ?queue: string
      bare_run: boolean
      config: { key/value }
    }
    Output:
    lite_pipeline
    """
    @defer.inlineCallbacks
    def _createPipeline(request):
        taskName = yield tasks_tx.createTaskAndSave('runPipelines', 0)
                                                    

        # The name of a pipeline is being stored as a checksum.  Pipeline names
        # are arbitrary and the user will likely never know or care what it is.
        # The pipeline name still exists though because other tools will likely
        # find it useful to refer to a pipeline by a particular name, but if
        # we decide to change the pipeline name to something more meaningful they
        # won't have to chagne their code to use pipelineName instead of checksum
        if request.body['bare_run']:
            protocol = request.body['config']['pipeline.PIPELINE_TEMPLATE']
        else:
            protocol = 'clovr_wrapper'
            request.body['config']['pipeline.PIPELINE_WRAPPER_NAME'] = request.body['config']['pipeline.PIPELINE_NAME']
            
        defer.returnValue(persist.Pipeline(pipelineId=None,
                                           pipelineName=checksum,
                                           userName=request.body['user_name'],
                                           protocol=protocol,
                                           checksum=checksum,
                                           taskName=taskName,
                                           queue=request.body.get('queue', 'pipelinewrapper.q'),
                                           children=[],
                                           config=request.body['config']))


    @defer.inlineCallbacks
    def _startRemotePipeline(request):
        cluster = yield clusters_client.loadCluster(request.body['cluster'],
                                                    request.body['user_name'])

        # Forward the request on to the remote cluster, set parent_pipeline to None
        ret = yield pipelines_www_client.runPipeline(cluster['master']['public_dns'],
                                                     'local',
                                                     request.body['user_name'],
                                                     None,
                                                     request.body['bare_run'],
                                                     request.body.get('queue', 'pipelinewrapper.q'),
                                                     request.body['config'])

        defer.returnValue(ret)

    
    # If the parent pipeline is set and doesn't exist, error
    if request.body.get('parent_pipeline'):
        parentPipelines = yield persist.loadAllPipelinesBy({'pipeline_name': request.body['parent_pipeline']},
                                                           request.body['user_name'])
        if not parentPipelines:
            raise InvalidParentPipeline(request.body['parent_pipeline'])

        if len(parentPipelines) == 1:
            parentPipeline = parentPipelines[0]
        else:
            raise Exception('More than one possible parent pipeline choice, not sure what to do here')
    else:
        parentPipeline = None


    if request.body['cluster'] == 'local':
        checksum = _checksumInput(request)

        errors = yield _validatePipelineConfig(request)

        if errors:
            raise InvalidPipelineConfig('Configuration did not pass validation')

        request.body['config']['pipeline.PIPELINE_NAME'] = checksum
        
        protocol = 'clovr_wrapper' if not request.body['bare_run'] else request.body['config']['pipeline.PIPELINE_TEMPLATE']
        
        try:
            existingPipeline = yield persist.loadPipelineBy({'checksum': checksum,
                                                             'protocol': protocol},
                                                            request.body['user_name'])
            pipelineLite = yield _pipelineToDictLite(request.state.machineconf,
                                                     existingPipeline)
            defer.returnValue(request.update(response=pipelineLite))
        except persist.PipelineNotFoundError:
            pipeline = yield _createPipeline(request)
            yield persist.savePipeline(pipeline)
            pipelineLite = yield _pipelineToDictLite(request.state.machineconf,
                                                     pipeline)
            # We want to do a deeper validation of the configuration and then run the pipeline.
            # Then we want to monitor it both through the ergatis observer and a timed update
            # of any children it has.
            #
            # We are going to do all this work in the background so we can exit the
            # handler.  Since incoming requests are rate-limited, we don't want to
            # block the handler for too long.  In this case we weren't pushing the
            # request and pipleine onto the queue for another handler to pick up
            # like we do in many other cases because we don't have to.  Deeper
            # validation is through a tasklet which is rate limited and submitting
            # a pipeline and monitoring it are all fairly light operations.  This
            # is somewhat lazy, and can be easily fixed in the future if it is an issue
            d = _deepValidation(request, pipeline)
            d.addCallback(lambda p : _runPipeline(request, p))
            d.addCallback(lambda p : persist.savePipeline(p).addCallback(lambda _ : p))
            d.addCallback(lambda p : _monitor(request, p))
            d.addErrback(lambda f : tasks_tx.updateTask(pipeline.taskName,
                                                        lambda t : t.setState(tasks_tx.task.TASK_FAILED).addFailure(f)))

            if parentPipeline:
                parentPipeline = parentPipeline.update(children=parentPipeline.children + [('local',
                                                                                            pipeline.pipelineName)])
                yield persist.savePipeline(parentPipeline)

            defer.returnValue(request.update(response=pipelineLite))
    else:
        pipelineLite = yield _startRemotePipeline(request)

        childPipeline = [(request.body['cluster'],
                          pipelineLite['pipeline_name'])]
        
        if parentPipeline and childPipeline not in parentPipeline.children:
            parentPipeline = parentPipeline.update(children=parentPipeline.children + childPipeline)
            yield persist.savePipeline(parentPipeline)

        defer.returnValue(request.update(response=pipelineLite))


@defer.inlineCallbacks
def handleWWWResumePipeline(request):
    pipeline = yield persist.loadPipelineBy({'pipeline_name': request.body['pipeline_name']},
                                             request.body['user_name'])
    yield pipeline_run.resume(pipeline)
    #
    # Give it a few seconds for the pipeline to startup again
    yield defer_utils.sleep(5)()
    yield _monitor(request, pipeline)

    pipelineLite = yield _pipelineToDictLite(request.state.machineconf,
                                             pipeline)
    defer.returnValue(request.update(response=pipelineLite))
        
def handleWWWObserver(request):
    """
    Input:
    { id: string
      file: string
      event: string
      retval: string
      props: string
      host: string
      time: string
      name: string
      message: string
    }

    Output:
    None
    """
    request.mq.send('/queue/pipelines/observer/' + request.body['props'],
                    json.dumps(request.body))
    return defer_pipe.ret(request.update(response=None))

@defer.inlineCallbacks
def handleWWWUpdatePipelineConfig(request):
    """
    Sets the config section of a pipeline exactly to what is given
    Input:
    { cluster: string
      user_name: string
      criteria: { key/valie }
      config: { key/value }
    }

    Output:
    None
    """
    pipelines = yield persist.loadAllPipelinesBy(request.body['criteria'],
                                                 request.body['user_name'])
    if len(pipelines) == 1:
        p = pipelines[0].update(config=config.configFromMap(request.body['config']))
        yield persist.savePipeline(p)
    else:
        raise Exception('More than one pipelines matches provided criteria: ' + repr(request.body['criteria']))

    defer.returnValue(request.update(response=None))

@defer.inlineCallbacks
def handleWWWValidatePipelineConfig(request):
    """
    This is limited to simple type checks.
    
    Input:
    { cluster: string
      bare_run: boolean
      config: { key/value }
    }
    Output:
    { errors: [{ message: string, keys: [string] }]
    }
    """
    errors = yield _validatePipelineConfig(request)
    defer.returnValue(request.update(response={'errors': errors}))
    

@defer.inlineCallbacks
def handleWWWPipelineStatus(request):
    """
    Input:
    { cluster: string
      user_name: string
      criteria: { key/value }
    }
    Output:
    pipeline
    """
    pipeline = yield persist.loadPipelineBy(request.body['criteria'],
                                            request.body['user_name'])
    pipelineLite = yield _pipelineToDictLite(request.state.machineconf,
                                             pipeline)
    pipelineLite = func.updateDict(pipelineLite,
                                   {'config': config.configToDict(pipeline.config)})
    defer.returnValue(request.update(response=pipelineLite))

@defer.inlineCallbacks
def handleWWWListPipelines(request):
    """
    Input:
    { cluster: string
      user_name: string
    }
    Returns:
    lite_pipeline
    """
    pipelines = yield persist.loadAllPipelinesBy({},
                                                 request.body['user_name'])
    pipelinesLite = yield defer_utils.mapSerial(lambda p : _pipelineToDictLite(request.state.machineconf,
                                                                               p),
                                                pipelines)
    defer.returnValue(request.update(response=pipelinesLite))

def handleWWWListProtocols(request):
    """
    Input:
    { cluster: string
      ?verbose: boolean
    }
    Output:
    [string]
    If verbose
    {string: [{key/value}]}
    """
    def _removeAlwaysHidden(protocolConfig):
        return [pc
                for pc in protocolConfig
                if pc[1].get('visibility') != 'always_hidden']

    
    protocols = protocol_format.protocols(request.state.machineconf)
    if not request.body.get('verbose'):
        return defer_pipe.ret(request.update(response=protocols))
    else:
        ret = {}
        for p in protocols:
            protocolConfig = (protocol_format.load(request.state.machineconf,
                                                   p) +
                              protocol_format.load(request.state.machineconf,
                                                   'clovr_wrapper'))
            ret[p] = [func.updateDict(c[1], {'name': c[0]})
                      for c in _removeAlwaysHidden(protocolConfig)]
            
        return defer_pipe.ret(request.update(response=ret))

def handleWWWProtocolConfig(request):
    """
    Input:
    { cluster: string,
      protocol: string
    }
    Output:
    { key/value }
    """
    def _removeAlwaysHidden(protocolConfig):
        return [pc
                for pc in protocolConfig
                if pc[1].get('visibility') != 'always_hidden']

    protocolConfig = (protocol_format.load(request.state.machineconf,
                                          request.body['protocol']) +
                      protocol_format.load(request.state.machineconf,
                                           'clovr_wrapper'))
    return defer_pipe.ret(request.update(response=_removeAlwaysHidden(protocolConfig)))


def forwardToCluster(conf, queueUrl):
    return queue.forwardRequestToCluster(conf('www.url_prefix') + '/' + os.path.basename(queueUrl))

@defer.inlineCallbacks
def _monitorAnyPipelines(mq, state):
    @defer.inlineCallbacks
    def _loadPipeline(p):
        pl = yield _pipelineToDictLite(state.machineconf, p)
        defer.returnValue((p, pl))
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

def _subscribeToQueues(mq, state):
    processRunPipeline = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                 'user_name',
                                                                                 'bare_run',
                                                                                 'config']),
                                                               _containsPipelineTemplate,
                                                               handleWWWRunPipeline]))
    queue.subscribe(mq,
                    state.conf('pipelines.runpipeline_www'),
                    state.conf('pipelines.concurrent_runpipeline'),
                    queue.wrapRequestHandler(state, processRunPipeline))
    

    processResumePipeline = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                    'user_name',
                                                                                    'pipeline_name']),
                                                                        forwardToCluster(state.conf,
                                                                                         state.conf('pipelines.resumepipeline_www')),                                                                  
                                                                  handleWWWResumePipeline]))
    queue.subscribe(mq,
                    state.conf('pipelines.resumepipeline_www'),
                    state.conf('pipelines.concurrent_resumepipeline'),
                    queue.wrapRequestHandler(state, processResumePipeline))

    
    processObserver = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['id',
                                                                              'file',
                                                                              'event',
                                                                              'retval',
                                                                              'props',
                                                                              'host',
                                                                              'time',
                                                                              'name',
                                                                              'message']),
                                                            handleWWWObserver]))
    queue.subscribe(mq,
                    state.conf('pipelines.observer_www'),
                    state.conf('pipelines.concurrent_observer'),
                    queue.wrapRequestHandler(state, processObserver))

    processUpdatePipelineConfig = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                          'user_name',
                                                                                          'criteria',
                                                                                          'config']),
                                                                        forwardToCluster(state.conf,
                                                                                         state.conf('pipelines.updatepipelineconfig_www')),
                                                                        handleWWWUpdatePipelineConfig]))
    queue.subscribe(mq,
                    state.conf('pipelines.updatepipelineconfig_www'),
                    state.conf('pipelines.concurrent_updatepipelineconfig'),
                    queue.wrapRequestHandler(state, processUpdatePipelineConfig))

    
    processValidatePipelineConfig = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                            'bare_run',
                                                                                            'config']),
                                                                          _containsPipelineTemplate,
                                                                          forwardToCluster(state.conf,
                                                                                           state.conf('pipelines.validatepipelineconfig_www')),
                                                                          handleWWWValidatePipelineConfig]))
    queue.subscribe(mq,
                    state.conf('pipelines.validatepipelineconfig_www'),
                    state.conf('pipelines.concurrent_validatepipelineconfig'),
                    queue.wrapRequestHandler(state, processValidatePipelineConfig))


    processPipelineStatus = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                    'user_name',
                                                                                    'criteria']),
                                                                  forwardToCluster(state.conf, state.conf('pipelines.pipelinestatus_www')),
                                                                  handleWWWPipelineStatus]))
    queue.subscribe(mq,
                    state.conf('pipelines.pipelinestatus_www'),
                    state.conf('pipelines.concurrent_pipelinestatus'),
                    queue.wrapRequestHandler(state, processPipelineStatus))

    
    processListPipelines = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                   'user_name']),
                                                                 forwardToCluster(state.conf, state.conf('pipelines.listpipelines_www')),
                                                                 handleWWWListPipelines]))
    queue.subscribe(mq,
                    state.conf('pipelines.listpipelines_www'),
                    state.conf('pipelines.concurrent_listpipelines'),
                    queue.wrapRequestHandler(state, processListPipelines))

    
    processListProtocols = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                   'user_name']),
                                                                 forwardToCluster(state.conf, state.conf('pipelines.listprotocols_www')),
                                                                 handleWWWListProtocols]))
    queue.subscribe(mq,
                    state.conf('pipelines.listprotocols_www'),
                    state.conf('pipelines.concurrent_listprotocols'),
                    queue.wrapRequestHandler(state, processListProtocols))

    processProtocolConfig = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                    'protocol']),
                                                                  forwardToCluster(state.conf, state.conf('pipelines.protocolconfig_www')),
                                                                  handleWWWProtocolConfig]))
    queue.subscribe(mq,
                    state.conf('pipelines.protocolconfig_www'),
                    state.conf('pipelines.concurrent_protocolconfig'),
                    queue.wrapRequestHandler(state, processProtocolConfig))

def makeService(conf):
    mqService = client.makeService(conf)

    mqFactory = mqService.mqFactory

    # State is currently not used, but kept around for future purposes
    state = State(conf)

    d = _monitorAnyPipelines(mqFactory, state)
    d.addCallback(lambda _ : _subscribeToQueues(mqFactory, state))
    
    return mqService

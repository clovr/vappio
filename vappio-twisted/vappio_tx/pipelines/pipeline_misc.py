import os
import hashlib

from twisted.internet import defer

from igs.utils import functional as func

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.pipelines import pipeline_run
from vappio_tx.pipelines import protocol_format
from vappio_tx.pipelines import pipeline_validate
from vappio_tx.pipelines import pipeline_monitor

class Error(Exception):
    pass

def containsPipelineTemplate(request):
    if 'pipeline.PIPELINE_TEMPLATE' in request.body['config']:
        return defer_pipe.ret(request)
    else:
        raise Error('Must provide a config with pipeline.PIPELINE_TEMPLATE')

def validatePipelineConfig(request):
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

def checksumInput(request):
    keys = [k
            for k in request.body['config'].keys()
            if k.startswith('input.') or k.startswith('params.') or k == 'pipeline.PIPELINE_TEMPLATE']
    keys.sort()

    valuesCombined = ','.join([request.body['config'][k] for k in keys])

    return hashlib.md5(valuesCombined).hexdigest()

    
def deepValidation(request, pipeline):
    # Add stuff here
    return defer.succeed(pipeline)

def runPipeline(request, pipeline):
    runState = func.Record(conf=request.state.conf,
                           machineconf=request.state.machineconf,
                           mq=request.mq)
    return pipeline_run.run(runState, pipeline)

def monitor_run(request, pipeline):
    monitorState = pipeline_monitor.MonitorState(request.state.conf,
                                                 request.state.machineconf,
                                                 request.mq,
                                                 pipeline,
                                                 int(request.state.conf('pipelines.retries')))
    return pipeline_monitor.monitor_run(monitorState, resume)

def monitor_resume(request, pipeline):
    monitorState = pipeline_monitor.MonitorState(request.state.conf,
                                                 request.state.machineconf,
                                                 request.mq,
                                                 pipeline,
                                                 int(request.state.conf('pipelines.retries')))
    return pipeline_monitor.monitor_resume(monitorState)

def forwardToCluster(conf, queueUrl):
    return queue.forwardRequestToCluster(conf('www.url_prefix') + '/' + os.path.basename(queueUrl))



import os

from twisted.internet import defer

from igs.utils import logging

from igs_tx import workflow_runner

from igs_tx.utils import global_state
from igs_tx.utils import defer_utils

from vappio_tx.pipelines import pipeline_misc

from vappio_tx.www_client import tags as tags_client
from vappio_tx.www_client import pipelines as pipelines_client
from vappio_tx.www_client import tasks as tasks_client

from vappio_tx.tasks import tasks

TMP_DIR='/tmp'

PRESTART_STATE = 'prestart'
PRERUN_STATE = 'prerun'
RUN_PIPELINE_STATE = 'run_pipeline'
RUNNING_PIPELINE_STATE = 'running_pipeline'
POSTRUN_STATE = 'postrun'
COMPLETED_STATE = 'completed'
FAILED_STATE = 'failed'

TAG_FILE_ACTION = 'TAG_FILE'
TAG_URL_ACTION = 'TAG_URL'
TAG_METADATA_ACTION = 'TAG_METADATA'
CONFIG_ACTION = 'CONFIG'


def _log(batchState, msg):
    logging.logPrint('BATCH_NUM %d - %s' % (batchState['batch_num'], msg))

@defer.inlineCallbacks
def _createTags(actions):
    tags = {}
    for action in actions:
        if action['action'] == TAG_FILE_ACTION:
            tags[action['key']].setdefault('files', []).append(action['value'])
        elif action['action'] == TAG_URL_ACTION:
            tags[action['key']].setdefault('urls', []).append(action['value'])
        elif action['action'] == TAG_METADATA_ACTION:
            k, v = action['value'].split('=', 1)
            tags[action['key']].setdefault('metadata', {})[k] = v

    for tagName, values in tags.iteritems():
        yield tags_client.tagData('localhost',
                                  'local',
                                  'guest',
                                  'overwrite',
                                  tagName,
                                  values.get('files', []),
                                  values.get('metadata', []),
                                  False,
                                  False,
                                  False,
                                  values.get('urls', []))
        

def _applyConfig(pipelineConfig, actions):
    for action in actions:
        if action['action'] == CONFIG_ACTION:
            pipelineConfig[action['key']] = action['value']

    return pipelineConfig
        
@defer.inlineCallbacks
def _applyActions(innerPipelineConfig, actions):
    yield _createTags(actions)
    defer.returnValue(_applyConfig(innerPipelineConfig, actions))


def _writeErgatisConfig(pipelineConfig, outputFile):
    fout = open(outputFile, 'w')
    
    # We want to produce an ini like file with [section]'s
    sections = {}
    for k in pipelineConfig.keys():
        sections.setdefault('.'.join(k.split('.')[:-1]), []).append(k)

    for s, ks in sections.iteritems():
        if s not in ['', 'env']:        
            fout.write('[' + s + ']\n')
            for k in ks:
                shortK = k.split('.')[-1]
                fout.write('%s=%s\n' % (shortK, str(pipelineConfig[k])))

    fout.close()    

@defer.inlineCallbacks
def _waitForPipeline(batchState):
    while True:
        task = yield tasks_client.loadTask('localhost',
                                           batchState['pipeline_config']['cluster.CLUSTER_NAME'],
                                           'guest',
                                           batchState['pipeline_task'])
        if task['state'] == 'completed':
            break
        elif task['state'] == 'failed':
            raise Exception('Task failed - %s' % batchState['pipeline_task'])

        yield defer_utils.sleep(30)()
        
    
@defer.inlineCallbacks
def _run(state, batchState):
    if 'state' not in batchState:
        _log(batchState, 'First time running, creating pipeline state information')
        batchState['pipeline_config'] = yield _applyActions(state.innerPipelineConfig(),
                                                            batchState['actions'])
        batchState['state'] = PRESTART_STATE

        # We need to create a fake, local, pipeline for metrics to work
        batchState['pipeline_name'] = pipeline_misc.checksumInput(batchState['pipeline_config'])
        batchState['pipeline_config']['pipeline.PIPELINE_NAME'] = batchState['pipeline_name']
        batchState['pipeline_config']['pipeline.PIPELINE_WRAPPER_NAME'] = batchState['pipeline_name']
        
        pipeline = yield pipelines_client.createPipeline('localhost',
                                                         'local',
                                                         'guest',
                                                         batchState['pipeline_name'],
                                                         'clovr_wrapper',
                                                         'pipeline.q',
                                                         batchState['pipeline_config'])

        batchState['clovr_wrapper_task_name'] = pipeline['task_name']

        _log(batchState, 'Setting number of tasks to 6 (number in a standard clovr_wrapper)')
        
        state.updateBatchState()
    else:
        _log(batchState, 'Pipeline run before, loading pipeline information')
        pipeline = yield pipelines_client.pipelineList('localhost',
                                                       'local',
                                                       'guest',
                                                       batchState['pipeline_name'],
                                                       detail=True)

    pipelineConfigFile = os.path.join(TMP_DIR, 'pipeline_configs', global_state.make_ref() + '.conf')
    
    _log(batchState, 'Creating ergatis configuration')
    _writeErgatisConfig(batchState['pipeline_config'], pipelineConfigFile)

    if batchState['state'] == PRESTART_STATE:
        _log(batchState, 'Pipeline is in PRESTART state')
        yield state.prerunQueue.addWithDeferred(workflow_runner.run,
                                                state.workflowConfig(),
                                                batchState['pipeline_config']['pipeline.PRESTART_TEMPLATE_XML'],
                                                pipelineConfigFile,
                                                TMP_DIR)
        batchState['state'] = PRERUN_STATE
        state.updateBatchState()


    if batchState['state'] == PRERUN_STATE:
        _log(batchState, 'Pipeline is in PRERUN state')
        yield state.prerunQueue.addWithDeferred(workflow_runner.run,
                                                state.workflowConfig(),
                                                batchState['pipeline_config']['pipeline.PRERUN_TEMPLATE_XML'],
                                                pipelineConfigFile,
                                                TMP_DIR)
        batchState['state'] = RUN_PIPELINE_STATE
        state.updateBatchState()
        

    if batchState['state'] == RUN_PIPELINE_STATE:
        _log(batchState, 'Pipeline is in RUN_PIPELINE state')
        pipeline = yield pipelines_client.runPipeline(host='localhost',
                                                      clusterName=batchState['pipeline_config']['cluster.CLUSTER_NAME'],
                                                      userName='guest',
                                                      parentPipeline=None,
                                                      bareRun=True,
                                                      queue=state.innerPipelineQueue(),
                                                      config=batchState['pipeline_config'],
                                                      overwrite=True)
        batchState['pipeline_task'] = pipeline['task_name']
        batchState['state'] = RUNNING_PIPELINE_STATE
        state.updateBatchState()


    if batchState['state'] == RUNNING_PIPELINE_STATE:
        _log(batchState, 'Pipeline is in RUNNING_PIPELINE state')
        yield _waitForPipeline(batchState)
        batchState['state'] = POSTRUN_STATE
        state.updateBatchState()

    if batchState['state'] == POSTRUN_STATE:
        _log(batchState, 'Pipeline is in POSTRUN state')
        yield state.postrunQueue.addWithDeferred(workflow_runner.run,
                                                 state.workflowConfig(),
                                                 batchState['pipeline_config']['pipeline.POSTRUN_TEMPLATE_XML'],
                                                 pipelineConfigFile,
                                                 TMP_DIR)
        batchState['state'] = COMPLETED_STATE
        state.updateBatchState()

    _log(batchState, 'Pipeline finished successfully')
    

@defer.inlineCallbacks
def run(state, batchState):
    try:
        yield _run(state, batchState)
    except:
        _log(batchState, 'There was an error in the pipeline, setting to failed')
        batchState['state'] = FAILED_STATE
        raise
    

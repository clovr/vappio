import os

from twisted.python import log

from twisted.internet import defer
from twisted.internet import reactor

from igs.utils import logging
from igs.utils import config

from igs_tx import workflow_runner

from igs_tx.utils import global_state
from igs_tx.utils import defer_utils
from igs_tx.utils import ssh

from vappio_tx.pipelines import pipeline_misc

from vappio_tx.www_client import tags as tags_client
from vappio_tx.www_client import clusters as clusters_client
from vappio_tx.www_client import pipelines as pipelines_client
from vappio_tx.www_client import tasks as tasks_client

from vappio_tx.tasks import tasks

AUTOSHUTDOWN_REFRESH = 20 * 60
CHILDREN_PIPELINE_REFRESH = 5 * 60
RETRIES = 3
TMP_DIR='/tmp'

PRESTART_STATE = 'prestart'
STARTING_STATE = 'starting'
PRERUN_STATE = 'prerun'
RUN_PIPELINE_STATE = 'run_pipeline'
RUNNING_PIPELINE_STATE = 'running_pipeline'
POSTRUN_STATE = 'postrun'

RUNNING_STATE = 'running'
COMPLETED_STATE = 'completed'
FAILED_STATE = 'failed'

TAG_FILE_ACTION = 'TAG_FILE'
TAG_URL_ACTION = 'TAG_URL'
TAG_METADATA_ACTION = 'TAG_METADATA'
CONFIG_ACTION = 'CONFIG'


class Error(Exception):
    pass

class TaskError(Error):
    pass

def _log(batchState, msg):
    logging.logPrint('BATCH_NUM %d - %s' % (batchState['batch_num'], msg))

@defer.inlineCallbacks
def _updateTask(batchState, f):
    if 'clovr_wrapper_task_name' in batchState:
        task = yield tasks.updateTask(batchState['clovr_wrapper_task_name'], f)

        # This is cheap, but we need a way for the pipelines cache to realize
        # the pipeline we just modified the task for has been changed. We do
        # this by loading the config and resaving it, which cause an invalidation
        # in the cache.  There is not a more direct way for an outside process
        # to cause an invalidation yet.
        pipeline = yield pipelines_client.pipelineList('localhost',
                                                       'local',
                                                       'guest',
                                                       batchState['pipeline_name'],
                                                       detail=True)

        pipeline = pipeline[0]
        yield pipelines_client.updateConfigPipeline('localhost',
                                                    'local',
                                                    'guest',
                                                    {'pipeline_name': batchState['pipeline_name']},
                                                    pipeline['config'])

        defer.returnValue(task)
    

    
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
        if task['state'] == tasks.task.TASK_COMPLETED:
            break
        elif task['state'] == tasks.task.TASK_FAILED:
            raise Exception('Task failed - %s' % batchState['pipeline_task'])

        yield defer_utils.sleep(30)()
        

@defer.inlineCallbacks
def _monitorPipeline(batchState):
    """
    Monitors the current pipeline, propogating its children state to it
    """
    pl = yield pipelines_client.pipelineList('localhost',
                                             'local',
                                             'guest',
                                             batchState['pipeline_name'],
                                             True)
    pl = pl[0]


    numTasks = 6
    completedTasks = 4
    for cl, pName in pl['children']:
        try:
            _log(batchState, 'Loading child pipeline: (%s, %s)' % (cl, pName))
            remotePipelines = yield pipelines_client.pipelineList('localhost',
                                                                  cl,
                                                                  'guest',
                                                                  pName,
                                                                  True)
            remotePipeline = remotePipelines[0]
            _log(batchState, 'Loading task for child pipeline: %s' % remotePipeline['task_name'])
            remoteTask = yield tasks_client.loadTask('localhost',
                                                     cl,
                                                     'guest',
                                                     remotePipeline['task_name'])

            numTasks += remoteTask['numTasks']
            completedTasks += remoteTask['completedTasks']
        except Exception, err:
            _log(batchState, 'Error in monitorPipeline: %s' % str(err))

    if pl['children']:
        _log(batchState, 'Updating task with numSteps=%d completedSteps=%d' % (numTasks, completedTasks))
        yield _updateTask(batchState,
                          lambda t : t.update(numTasks=numTasks,
                                              completedTasks=completedTasks))

    if batchState['pipeline_state'] == RUNNING_PIPELINE_STATE:
        reactor.callLater(CHILDREN_PIPELINE_REFRESH, _monitorPipeline, batchState)


@defer.inlineCallbacks
def _delayAutoshutdown(state, batchState):
    _log(batchState, 'AUTOSHUTDOWN: Trying to touch autoshutdown file')
    try:
        cluster = yield clusters_client.loadCluster('localhost',
                                                    batchState['pipeline_config']['cluster.CLUSTER_NAME'],
                                                    'guest')

        if batchState.get('state', None) == COMPLETED_STATE:
            _log(batchState, 'AUTOSHUTDOWN: Pipeline complete, done')
        if batchState.get('state', None) != RUNNING_STATE:
            _log(batchState, 'AUTOSHUTDOWN: Pipeline not running, calling later')
            reactor.callLater(AUTOSHUTDOWN_REFRESH, _delayAutoshutdown, state, batchState)
        elif cluster['state'] == 'running':
            # We need the SSH options from the machine.conf, ugh I hate these OOB dependencies
            conf = config.configFromStream(open('/tmp/machine.conf'))
            
            _log(batchState, 'AUTOSHUTDOWN: Touching delayautoshutdown')
            yield ssh.runProcessSSH(cluster['master']['public_dns'],
                                    'touch /var/vappio/runtime/delayautoshutdown',
                                    stdoutf=None,
                                    stderrf=None,
                                    sshUser=conf('ssh.user'),
                                    sshFlags=conf('ssh.options'),
                                    log=True)
            _log(batchState, 'AUTOSHUTDOWN: Setting up next call')
            reactor.callLater(AUTOSHUTDOWN_REFRESH, _delayAutoshutdown, state, batchState)
        else:
            _log(batchState, 'AUTOSHUTDOWN: Cluster not running, calling later')
            reactor.callLater(AUTOSHUTDOWN_REFRESH, _delayAutoshutdown, state, batchState)

    except:
        _log(batchState, 'AUTOSHUTDOWN: Cluster does not exist, calling later')
        reactor.callLater(AUTOSHUTDOWN_REFRESH, _delayAutoshutdown, state, batchState)
        
@defer.inlineCallbacks
def _run(state, batchState):
    if 'state' not in batchState:
        _log(batchState, 'First time running, creating pipeline state information')
        batchState['pipeline_config'] = yield _applyActions(state.innerPipelineConfig(),
                                                            batchState['actions'])
        batchState['pipeline_state'] = PRESTART_STATE

        # We need to create a fake, local, pipeline for metrics to work
        batchState['pipeline_name'] = pipeline_misc.checksumInput(batchState['pipeline_config'])
        batchState['pipeline_config']['pipeline.PIPELINE_NAME'] = batchState['pipeline_name']
        batchState['pipeline_config']['pipeline.PIPELINE_WRAPPER_NAME'] = batchState['pipeline_name']

        _log(batchState, 'Pipeline named ' + batchState['pipeline_name'])
        
        pipeline = yield pipelines_client.createPipeline(host='localhost',
                                                         clusterName='local',
                                                         userName='guest',
                                                         pipelineName=batchState['pipeline_name'],
                                                         protocol='clovr_wrapper',
                                                         queue='pipeline.q',
                                                         config=batchState['pipeline_config'],
                                                         parentPipeline=state.parentPipeline())

        batchState['clovr_wrapper_task_name'] = pipeline['task_name']

        _log(batchState, 'Setting number of tasks to 6 (number in a standard clovr_wrapper)')
        yield _updateTask(batchState,
                          lambda t : t.update(completedTasks=0,
                                              numTasks=6))
        
        state.updateBatchState()
    else:
        _log(batchState, 'Pipeline run before, loading pipeline information')
        pipeline = yield pipelines_client.pipelineList('localhost',
                                                       'local',
                                                       'guest',
                                                       batchState['pipeline_name'],
                                                       detail=True)

    batchState['state'] = RUNNING_STATE

    yield _updateTask(batchState,
                      lambda t : t.setState(tasks.task.TASK_RUNNING))
    
    pipelineConfigFile = os.path.join(TMP_DIR, 'pipeline_configs', global_state.make_ref() + '.conf')
    
    _log(batchState, 'Creating ergatis configuration')
    _writeErgatisConfig(batchState['pipeline_config'], pipelineConfigFile)

    if batchState['pipeline_state'] == PRESTART_STATE:
        _log(batchState, 'Pipeline is in PRESTART state')
        yield state.prerunQueue.addWithDeferred(workflow_runner.run,
                                                state.workflowConfig(),
                                                batchState['pipeline_config']['pipeline.PRESTART_TEMPLATE_XML'],
                                                pipelineConfigFile,
                                                TMP_DIR)

        yield _updateTask(batchState,
                          lambda t : t.addMessage(tasks.task.MSG_SILENT,
                                                  'Completed prestart'
                                                  ).progress())
                               
        batchState['pipeline_state'] = STARTING_STATE
        state.updateBatchState()

    if batchState['pipeline_state'] == STARTING_STATE:
        _log(batchState, 'Pipeline is in STARTING state')
        clusterTask = yield clusters_client.startCluster('localhost',
                                                         batchState['pipeline_config']['cluster.CLUSTER_NAME'],
                                                         'guest',
                                                         int(batchState['pipeline_config']['cluster.EXEC_NODES']),
                                                         0,
                                                         batchState['pipeline_config']['cluster.CLUSTER_CREDENTIAL'],
                                                         {'cluster.master_type': batchState['pipeline_config']['cluster.MASTER_INSTANCE_TYPE'],
                                                          'cluster.master_bid_price': batchState['pipeline_config']['cluster.MASTER_BID_PRICE'],
                                                          'cluster.exec_type': batchState['pipeline_config']['cluster.EXEC_INSTANCE_TYPE'],
                                                          'cluster.exec_bid_price': batchState['pipeline_config']['cluster.EXEC_BID_PRICE']})

        taskState = yield tasks.blockOnTask('localhost',
                                            'local',
                                            clusterTask)

        if taskState != tasks.task.TASK_COMPLETED:
            raise TaskError(clusterTask)
        
        yield _updateTask(batchState,
                          lambda t : t.addMessage(tasks.task.MSG_SILENT,
                                                  'Completed start'
                                                  ).progress())

        batchState['pipeline_state'] = PRERUN_STATE
        state.updateBatchState()


    if batchState['pipeline_state'] == PRERUN_STATE:
        _log(batchState, 'Pipeline is in PRERUN state')
        yield state.prerunQueue.addWithDeferred(workflow_runner.run,
                                                state.workflowConfig(),
                                                batchState['pipeline_config']['pipeline.PRERUN_TEMPLATE_XML'],
                                                pipelineConfigFile,
                                                TMP_DIR)

        yield _updateTask(batchState,
                          lambda t : t.addMessage(tasks.task.MSG_SILENT,
                                                  'Completed prerun'
                                                  ).progress())
        batchState['pipeline_state'] = RUN_PIPELINE_STATE
        state.updateBatchState()
        

    if batchState['pipeline_state'] == RUN_PIPELINE_STATE:
        _log(batchState, 'Pipeline is in RUN_PIPELINE state')
        pipeline = yield pipelines_client.runPipeline(host='localhost',
                                                      clusterName=batchState['pipeline_config']['cluster.CLUSTER_NAME'],
                                                      userName='guest',
                                                      parentPipeline=batchState['pipeline_name'],
                                                      bareRun=True,
                                                      queue=state.innerPipelineQueue(),
                                                      config=batchState['pipeline_config'],
                                                      overwrite=True)
        batchState['pipeline_task'] = pipeline['task_name']

        yield _updateTask(batchState,
                          lambda t : t.addMessage(tasks.task.MSG_SILENT,
                                                  'Completed run pipeline'
                                                  ).progress())
        batchState['pipeline_state'] = RUNNING_PIPELINE_STATE
        state.updateBatchState()


    if batchState['pipeline_state'] == RUNNING_PIPELINE_STATE:
        _log(batchState, 'Pipeline is in RUNNING_PIPELINE state')
        _monitorPipeline(batchState)
        yield _waitForPipeline(batchState)

        yield _updateTask(batchState,
                          lambda t : t.addMessage(tasks.task.MSG_SILENT,
                                                  'Completed running pipeline'
                                                  ).progress())
        batchState['pipeline_state'] = POSTRUN_STATE
        state.updateBatchState()

    if batchState['pipeline_state'] == POSTRUN_STATE:
        _log(batchState, 'Pipeline is in POSTRUN state')
        yield state.postrunQueue.addWithDeferred(workflow_runner.run,
                                                 state.workflowConfig(),
                                                 batchState['pipeline_config']['pipeline.POSTRUN_TEMPLATE_XML'],
                                                 pipelineConfigFile,
                                                 TMP_DIR)

        yield _updateTask(batchState,
                          lambda t : t.addMessage(tasks.task.MSG_SILENT,
                                                  'Completed postrun'
                                                  ).progress())
                                                   
        batchState['pipeline_state'] = COMPLETED_STATE
        batchState['state'] = COMPLETED_STATE
        state.updateBatchState()

    yield _updateTask(batchState,
                      lambda t : t.setState(tasks.task.TASK_COMPLETED))
    _log(batchState, 'Pipeline finished successfully')
    

def _runWrapper(state, batchState):
    batchState.setdefault('retry_count', RETRIES)
    d = _run(state, batchState)

    @defer.inlineCallbacks
    def _errback(f):
        _log(batchState, 'There was an error in the pipeline, setting to failed')
        log.err(f)
        batchState['state'] = FAILED_STATE
        yield _updateTask(batchState,
                          lambda t : t.setState(tasks.task.TASK_FAILED))
        state.updateBatchState()
        batchState['retry_count'] -= 1
        if batchState['retry_count'] > 0:
            yield run(state, batchState)
        else:
            # Since we are giving up, reset the counter so the next time we are called
            # we will retry again
            batchState['retry_count'] = RETRIES
            state.updateBatchState()
            defer.returnValue(f)

    d.addErrback(_errback)
    return d
    
def run(state, batchState):
    _delayAutoshutdown(state, batchState)
    return _runWrapper(state, batchState)

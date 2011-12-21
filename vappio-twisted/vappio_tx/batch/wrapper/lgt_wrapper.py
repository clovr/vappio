import os

from twisted.python import log

from twisted.internet import defer
from twisted.internet import reactor

from igs.utils import logging
from igs.utils import config

from igs_tx.utils import global_state
from igs_tx.utils import defer_utils
from igs_tx.utils import commands
from igs_tx.utils import ssh
from igs_tx.utils import rsync

from vappio_tx.pipelines import pipeline_misc

from vappio_tx.www_client import tags as tags_client
from vappio_tx.www_client import clusters as clusters_client
from vappio_tx.www_client import pipelines as pipelines_client
from vappio_tx.www_client import tasks as tasks_client

from vappio_tx.tasks import tasks

RSYNC = ['rsync',
         '-rlptD',
         '-e', 'ssh -o PasswordAuthentication=no -o ConnectTimeout=30 -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o UserKnownHostsFile=/dev/null -i /mnt/keys/devel1.pem']


AUTOSHUTDOWN_REFRESH = 20 * 60
RESIZE_REFRESH = 10 * 60
CHILDREN_PIPELINE_REFRESH = 5 * 60
RETRIES = 100
TMP_DIR='/tmp'

STARTCLUSTER_STATE = 'startcluster_state'
REMOTE_LOCAL_TRANSFER_STATE = 'remote_local_transfer_state'
DECRYPT_STATE = 'decrypt_state'
REFERENCE_TRANSFER_STATE = 'reference_transfer_state'
RUN_PIPELINE_STATE = 'run_pipeline_state'
RUNNING_PIPELINE_STATE = 'running_pipeline_state'
HARVEST_STATE = 'harvest_state'
SHUTDOWN_STATE = 'shutdown_state'

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


def _decryptTagName(batchState):
    return 'lgt_input_batch_%d' % batchState['batch_num']


def _getOutput(batchState, command, *args, **kwargs):
    _log(batchState, 'CMD: ' + ' '.join(command))
    return commands.getOutput(command, *args, **kwargs)

@defer.inlineCallbacks
def _blockOnTask(taskName, cluster='local'):
    taskState = yield tasks.blockOnTask('localhost',
                                        cluster,
                                        taskName)
    
    if taskState != tasks.task.TASK_COMPLETED:
        raise TaskError(taskName)

    defer.returnValue(taskState)


@defer.inlineCallbacks
def _updateTask(batchState, f):
    if 'lgt_wrapper_task_name' in batchState:
        task = yield tasks.updateTask(batchState['lgt_wrapper_task_name'], f)

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


    numTasks = 9
    completedTasks = 6
    for cl, pName in pl['children']:
        try:
            remotePipelines = yield pipelines_client.pipelineList('localhost',
                                                                  cl,
                                                                  'guest',
                                                                  pName,
                                                                  True)
            remotePipeline = remotePipelines[0]
            _log(batchState, 'Loading child pipeline: (%s, %s, %s)' % (cl, pName, remotePipeline['task_name']))
            remoteTask = yield tasks_client.loadTask('localhost',
                                                     cl,
                                                     'guest',
                                                     remotePipeline['task_name'])

            numTasks += remoteTask['numTasks']
            completedTasks += remoteTask['completedTasks']
        except Exception, err:
            _log(batchState, 'Error in monitorPipeline: %s' % str(err))

    if pl['children']:
        yield _updateTask(batchState,
                          lambda t : t.update(numTasks=numTasks,
                                              completedTasks=completedTasks))

    if batchState['pipeline_state'] == RUNNING_PIPELINE_STATE:
        reactor.callLater(CHILDREN_PIPELINE_REFRESH, _monitorPipeline, batchState)


@defer.inlineCallbacks
def _remoteLocalTransfer(batchState):
    yield _getOutput(batchState,
                     ['rm', '-rf', batchState['pipeline_config']['params.DATA_DIRECTORY']],
                     log=True)
    yield _getOutput(batchState,
                     ['mkdir', '-p', batchState['pipeline_config']['params.DATA_DIRECTORY']],
                     log=True)
    
    for f in batchState['pipeline_config']['input.INPUT_FILES'].split(','):
        _log(batchState, 'Copying file: ' + f)

        rsyncOutputFile = os.path.join(batchState['pipeline_config']['params.DATA_DIRECTORY'],
                                       os.path.basename(f))
        
        src = (batchState['pipeline_config']['params.REMOTE_USER'] +
               '@' +
               batchState['pipeline_config']['params.REMOTE_HOST'] +
               ':' +
               f)
        
        rsyncCmd = RSYNC + [src, rsyncOutputFile]

        yield _getOutput(batchState,
                         rsyncCmd,
                         log=True)

    tag = yield tags_client.tagData(host='localhost',
                                    clusterName='local',
                                    userName='guest',
                                    action='overwrite',
                                    tagName=_decryptTagName(batchState),
                                    files=[batchState['pipeline_config']['params.DATA_DIRECTORY']],
                                    metadata={},
                                    recursive=True,
                                    expand=False,
                                    compressDir=None)

    _log(batchState, 'Waiting for tagging of %s to complete - %s' % (_decryptTagName(batchState),
                                                                     tag['task_name']))

    yield _blockOnTask(tag['task_name'])

    _log(batchState, 'Making sure cluster is up - ' + batchState['cluster_task'])
    
    yield _blockOnTask(batchState['cluster_task'])

    _log(batchState, 'Uploading query data')

    yield _getOutput(batchState,
                     ['vp-transfer-dataset',
                      '--tag-name=' + _decryptTagName(batchState),
                      '--dst-cluster=' + batchState['pipeline_config']['cluster.CLUSTER_NAME']],
                     log=True)

    # Clean up
    yield _getOutput(batchState,
                     ['rm', '-rf', batchState['pipeline_config']['params.DATA_DIRECTORY']],
                     log=True)
    
    yield _updateTask(batchState,
                      lambda t : t.addMessage(tasks.task.MSG_SILENT,
                                              'Completed start'
                                              ).progress())

@defer.inlineCallbacks
def _harvestTransfer(batchState):
    tagName = '%s_sam_files' % batchState['pipeline_name']
    outputName = 'lgt_batch_%03d_sam_files' % batchState['batch_num']
    
    yield _getOutput(batchState,
                     ['vp-transfer-dataset',
                      '--tag-name=' + tagName,
                      '--src-cluster=' + batchState['pipeline_config']['cluster.CLUSTER_NAME']],
                     log=True)


    tag = yield tags_client.loadTag('localhost',
                                    'local',
                                    'guest',
                                    tagName)
    
    dst = (batchState['pipeline_config']['params.REMOTE_USER'] +
           '@' +
           batchState['pipeline_config']['params.REMOTE_HOST'] +
           ':' +
           batchState['pipeline_config']['params.DATA_OUTPUT_DIRECTORY'] + '/' + outputName + '/')

    try:
        for f in tag['files']:
            rsyncCmd = RSYNC + [f, dst]
            yield _getOutput(batchState,
                             rsyncCmd,
                             log=True)
    finally:
        _getOutput(batchState,
                   ['vp-delete-dataset',
                    '--tag-name=' + tagName,
                    '--delete'],
                   log=True)
        

@defer.inlineCallbacks
def _delayAutoshutdown(state, batchState):
    _log(batchState, 'AUTOSHUTDOWN: Trying to touch autoshutdown file')
    if (('cluster_task' not in batchState or batchState.get('state', None) != RUNNING_STATE) and
        batchState.get('state', None) != COMPLETED_STATE):
        # Not ready yet
        _log(batchState, 'AUTOSHUTDOWN: No cluster or not running, calling later')
        reactor.callLater(AUTOSHUTDOWN_REFRESH, _delayAutoshutdown, state, batchState)
    elif ('cluster_task' in batchState and
          batchState.get('state', None) == RUNNING_STATE and
          batchState.get('pipeline_state', None) != SHUTDOWN_STATE):
        # Ready to see if resizing
        _log(batchState, 'AUTOSHUTDOWN: Making sure cluster is up')
        yield _blockOnTask(batchState['cluster_task'])

        try:
            cluster = yield clusters_client.loadCluster('localhost',
                                                        batchState['pipeline_config']['cluster.CLUSTER_NAME'],
                                                        'guest')
            
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
        except:
            pass

        _log(batchState, 'AUTOSHUTDOWN: Setting up next call')
        reactor.callLater(AUTOSHUTDOWN_REFRESH, _delayAutoshutdown, state, batchState)
    else:
        _log(batchState, 'AUTOSHUTDOWN: Giving up on this')
        
    
@defer.inlineCallbacks
def _keepClusterResized(state, batchState):
    _log(batchState, 'RESIZE: Checking if cluster must be resized')
    if (batchState.get('pipeline_state', None) != RUNNING_PIPELINE_STATE and
        batchState.get('state', None) != COMPLETED_STATE):
        
        _log(batchState, 'RESIZE: Cluster not started yet or pipeline not in running state, trying later')
        reactor.callLater(RESIZE_REFRESH, _keepClusterResized, state, batchState)
    elif batchState.get('pipeline_state', None) == RUNNING_PIPELINE_STATE:
        try:
            numExecs = len(batchState['pipeline_config']['input.INPUT_FILES'].split(','))

            yield _blockOnTask(batchState['cluster_task'])

            cluster = yield clusters_client.loadCluster('localhost',
                                                        batchState['pipeline_config']['cluster.CLUSTER_NAME'],
                                                        'guest')
            
            if len(cluster['exec_nodes']) < numExecs:
                _log(batchState, 'RESIZE: Adding more instances')
                output = yield _getOutput(batchState,
                                          ['vp-add-instances',
                                           '--num-exec=' + str(numExecs - len(cluster['exec_nodes'])),
                                           '--cluster=' + batchState['pipeline_config']['cluster.CLUSTER_NAME'],
                                           '-t'],
                                          log=True)

                batchState['add_instances_task'] = output['stdout'].strip()
                state.updateBatchState()
                yield _blockOnTask(batchState['add_instances_task'],
                                   cluster=batchState['pipeline_config']['cluster.CLUSTER_NAME'])
        except Exception, err:
            log.err(err)

        _log(batchState, 'RESIZE: Setting up next call')
        reactor.callLater(RESIZE_REFRESH, _keepClusterResized, state, batchState)
    else:
        _log(batchState, 'RESIZE: Not calling later')
        
    

@defer.inlineCallbacks
def _setQueue(batchState):
    yield _blockOnTask(batchState['cluster_task'])

    cluster = yield clusters_client.loadCluster('localhost',
                                                batchState['pipeline_config']['cluster.CLUSTER_NAME'],
                                                'guest')

    yield defer_utils.tryUntil(10,
                               lambda : _getOutput(batchState,
                                                   ['/opt/clovr_pipelines/workflow/project_saved_templates/clovr_lgt_wrapper/set_queue.sh',
                                                    cluster['master']['public_dns']],
                                                   log=True),
                               onFailure=defer_utils.sleep(2))
        
@defer.inlineCallbacks
def _run(state, batchState):
    if 'state' not in batchState:
        _log(batchState, 'First time running, creating pipeline state information')
        batchState['pipeline_config'] = yield _applyActions(state.innerPipelineConfig(),
                                                            batchState['actions'])
        batchState['pipeline_state'] = STARTCLUSTER_STATE

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

        batchState['lgt_wrapper_task_name'] = pipeline['task_name']

        _log(batchState, 'Setting number of tasks to 9 (number in a standard lgt_wrapper)')
        yield _updateTask(batchState,
                          lambda t : t.update(completedTasks=0,
                                              numTasks=9))
        
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

    if batchState['pipeline_state'] == STARTCLUSTER_STATE:
        _log(batchState, 'Pipeline is in STARTCLUSTER state')

        # First see if the cluster exists but is unresponsive
        try:
            cluster = yield clusters_client.loadCluster('localhost',
                                                        batchState['pipeline_config']['cluster.CLUSTER_NAME'],
                                                        'guest')
            if cluster['state'] == 'unresponsive':
                _log(batchState, 'Pipeline is unresponsive, terminating')
                terminateTask = yield clusters_client.terminateCluster('localhost',
                                                                       batchState['pipeline_config']['cluster.CLUSTER_NAME'],
                                                                       'guest')
                yield _blockOnTask(terminateTask)
        except:
            pass

        batchState['cluster_task'] = yield clusters_client.startCluster('localhost',
                                                                        batchState['pipeline_config']['cluster.CLUSTER_NAME'],
                                                                        'guest',
                                                                        int(batchState['pipeline_config']['cluster.EXEC_NODES']),
                                                                        0,
                                                                        batchState['pipeline_config']['cluster.CLUSTER_CREDENTIAL'],
                                                                        {'cluster.MASTER_INSTANCE_TYPE': batchState['pipeline_config']['cluster.MASTER_INSTANCE_TYPE'],
                                                                         'cluster.MASTER_BID_PRICE': batchState['pipeline_config']['cluster.MASTER_BID_PRICE'],
                                                                         'cluster.EXEC_INSTANCE_TYPE': batchState['pipeline_config']['cluster.EXEC_INSTANCE_TYPE'],
                                                                         'cluster.EXEC_BID_PRICE': batchState['pipeline_config']['cluster.EXEC_BID_PRICE']})

        yield _updateTask(batchState,
                          lambda t : t.update(completedTasks=0,
                                              numTasks=9))
        
        yield _updateTask(batchState,
                          lambda t : t.addMessage(tasks.task.MSG_SILENT,
                                                  'Completed startcluster'
                                                  ).progress())

        # Make sure autoshutdown is off
        _setQueue(batchState)
        
        batchState['pipeline_state'] = REMOTE_LOCAL_TRANSFER_STATE
        state.updateBatchState()

    if batchState['pipeline_state'] == REMOTE_LOCAL_TRANSFER_STATE:
        _log(batchState, 'Pipeline is in REMOTE_LOCAL_TRANSFER')
        yield state.prerunQueue.addWithDeferred(_remoteLocalTransfer,
                                                batchState)

        yield _updateTask(batchState,
                          lambda t : t.addMessage(tasks.task.MSG_SILENT,
                                                  'Completed remote_local_transfer'
                                                  ).progress())

        batchState['pipeline_state'] = DECRYPT_STATE
        state.updateBatchState()

    if batchState['pipeline_state'] == DECRYPT_STATE:
        _log(batchState, 'Pipeline is in DECRYPT')

        cluster = yield clusters_client.loadCluster('localhost',
                                                    batchState['pipeline_config']['cluster.CLUSTER_NAME'],
                                                    'guest')

        tag = yield tags_client.loadTag('localhost',
                                        batchState['pipeline_config']['cluster.CLUSTER_NAME'],
                                        'guest',
                                        _decryptTagName(batchState))

        conf = config.configFromStream(open('/tmp/machine.conf'))

        yield ssh.runProcessSSH(cluster['master']['public_dns'],
                                'mkdir -p /mnt/lgt_decrypt',
                                stdoutf=None,
                                stderrf=None,
                                sshUser=conf('ssh.user'),
                                sshFlags=conf('ssh.options'),
                                log=True)

        yield rsync.rsyncTo(cluster['master']['public_dns'],
                            batchState['pipeline_config']['params.DECRYPT_SCRIPT'],
                            '/mnt/',
                            options=conf('rsync.options'),
                            user=conf('rsync.user'),
                            log=True)
        
        for f in tag['files']:
            decryptCmd = ' '.join([os.path.join('/mnt', os.path.basename(batchState['pipeline_config']['params.DECRYPT_SCRIPT'])),
                                   f,
                                   '-out-dir', '/mnt/lgt_decrypt',
                                   '-remove-encrypted',
                                   '-password', batchState['pipeline_config']['params.DECRYPT_PASSWORD']])
                                       
            
            yield ssh.getOutput(cluster['master']['public_dns'],
                                decryptCmd,
                                sshUser=conf('ssh.user'),
                                sshFlags=conf('ssh.options'),
                                expected=[0, 253],
                                log=True)

        tag = yield tags_client.tagData(host='localhost',
                                        clusterName=batchState['pipeline_config']['cluster.CLUSTER_NAME'],
                                        userName='guest',
                                        action='overwrite',
                                        tagName=_decryptTagName(batchState),
                                        files=['/mnt/lgt_decrypt'],
                                        metadata={},
                                        recursive=True,
                                        expand=False,
                                        compressDir=None)

        _log(batchState, 'Waiting for tagging of %s to complete - %s' % (_decryptTagName(batchState),
                                                                         tag['task_name']))

        yield _blockOnTask(tag['task_name'],
                           cluster=batchState['pipeline_config']['cluster.CLUSTER_NAME'])
        
        yield _updateTask(batchState,
                          lambda t : t.addMessage(tasks.task.MSG_SILENT,
                                                  'Completed decrypt'
                                                  ).progress())

        batchState['pipeline_state'] = REFERENCE_TRANSFER_STATE
        state.updateBatchState()
        

    if batchState['pipeline_state'] == REFERENCE_TRANSFER_STATE:
        _log(batchState, 'Pipeline is in REFERENCE_TRANSFER state')
        
        transfers = []
        tags = (batchState['pipeline_config']['input.REF_TAG1'].split(',') +
                batchState['pipeline_config']['input.REF_TAG2'].split(','))
        for tag in tags:
            tag = tag.strip()
            output = yield _getOutput(batchState,
                                      ['vp-transfer-dataset',
                                       '-t',
                                       '--tag-name=' + tag,
                                       '--dst-cluster=' + batchState['pipeline_config']['cluster.CLUSTER_NAME']],
                                      log=True)
            
            transfers.append(output['stdout'].strip())

        for task in transfers:
            yield _blockOnTask(task)

        yield _updateTask(batchState,
                          lambda t : t.addMessage(tasks.task.MSG_SILENT,
                                                  'Completed reference_transfer'
                                                  ).progress())

        batchState['pipeline_state'] = RUN_PIPELINE_STATE
        state.updateBatchState()


    if batchState['pipeline_state'] == RUN_PIPELINE_STATE:
        _log(batchState, 'Pipeline is in RUN_PIPELINE state')
        batchState['pipeline_config']['input.INPUT_TAG'] = _decryptTagName(batchState)
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
        batchState['pipeline_state'] = HARVEST_STATE
        state.updateBatchState()

    if batchState['pipeline_state'] == HARVEST_STATE:
        _log(batchState, 'Pipeline is in HARVEST state')
        # Using prerunqueue because we want everything here serialized
        yield state.prerunQueue.addWithDeferred(_harvestTransfer,
                                                batchState)

        yield _updateTask(batchState,
                          lambda t : t.addMessage(tasks.task.MSG_SILENT,
                                                  'Completed harvest'
                                                  ).progress())
        
        batchState['pipeline_state'] = SHUTDOWN_STATE
        state.updateBatchState()

    if batchState['pipeline_state'] == SHUTDOWN_STATE:
        _log(batchState, 'Pipeline is in SHUTDOWN state')

        if 'add_instances_task' in batchState:
            try:
                yield _blockOnTask(batchState['add_instances_task'],
                                   cluster=batchState['pipeline_config']['cluster.CLUSTER_NAME'])
            except Exception, err:
                logging.errorPrint(str(err))
                log.err(err)

        yield clusters_client.terminateCluster('localhost',
                                               batchState['pipeline_config']['cluster.CLUSTER_NAME'],
                                               'guest')
        

        yield _updateTask(batchState,
                          lambda t : t.addMessage(tasks.task.MSG_SILENT,
                                                  'Completed shutdown'
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
        
        # Cheap right now because we are just always restarting the entire pipeline, hopefully
        # this doesn't happen very often though
        batchState['pipeline_state'] = STARTCLUSTER_STATE

        batchState['state'] = FAILED_STATE
        yield _updateTask(batchState,
                          lambda t : t.setState(tasks.task.TASK_FAILED))
        state.updateBatchState()
        batchState['retry_count'] -= 1
        if batchState['retry_count'] > 0:
            yield _runWrapper(state, batchState)
        else:
            # Since we are giving up, reset the counter so the next time we are called
            # we will retry again
            batchState['retry_count'] = RETRIES
            state.updateBatchState()
            defer.returnValue(f)

    d.addErrback(_errback)
    return d
    
def run(state, batchState):
    _keepClusterResized(state, batchState)
    _delayAutoshutdown(state, batchState)
    return _runWrapper(state, batchState)

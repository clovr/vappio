import os

from twisted.python import log

from twisted.internet import defer

from igs.utils import functional as func

from igs_tx.utils import defer_utils
from igs_tx.utils import defer_pipe
from igs_tx.utils import ssh
from igs_tx.utils import rsync
from igs_tx.utils import commands

from vappio_tx.utils import queue

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.tags import persist

from vappio_tx.www_client import clusters as www_clusters
from vappio_tx.www_client import tags as www_tags

from vappio_tx.tags import tag_mq_data

class Error(Exception):
    pass

class NoLocalClusterError(Error):
    pass

class RealizePhantomError(Error):
    pass

class TransferTagError(Error):
    pass

def _makeDirsOnCluster(cluster, dirNames):
    """
    Creates a series of directories on a cluster
    """
    @defer.inlineCallbacks
    def _createDir(d):
        yield ssh.runProcessSSH(cluster['master']['public_dns'],
                                'mkdir -p ' + d,
                                None,
                                log.err,
                                cluster['config']['ssh.user'],
                                cluster['config']['ssh.options'])
        try:
            if cluster['master']['instance_type'] is not None:
                yield ssh.runProcessSSH(cluster['master']['public_dns'],
                                        'chown -R %s %s' % (cluster['config']['vappio.user'],
                                                            d),
                                        None,
                                        log.err,
                                        cluster['config']['ssh.user'],
                                        cluster['config']['ssh.options'])
        except commands.Error:
            pass
        
    return defer_utils.mapSerial(_createDir, dirNames)


def _makePathRelative(path):
    if path and path[0] == '/':
        return path[1:]
    else:
        return path

def _removeBase(baseDir, f):
    if baseDir[-1] != '/':
        baseDir += '/'

    if f.startswith(baseDir):
        return f.replace(baseDir, '', 1)

    return f

def _partitionFiles(files, baseDir):
    if baseDir:
        baseDirFiles = [_makePathRelative(_removeBase(baseDir, f))
                        for f in files
                        if f.startswith(baseDir)]
        downloadFiles = [_makePathRelative(f)
                         for f in files
                         if not f.startswith(baseDir)]
        return (baseDirFiles, downloadFiles)
    else:
        return ([], files)

@defer.inlineCallbacks
def _realizeUrls(request):
    localTag = yield request.state.tagPersist.loadTag(request.body['tag_name'])
    
    # If we have urls we create a fake phantom tag
    fakePhantom = {'cluster.ALL.command':
                   'reliableDownloader.py -m 300 -t 20 -b ${base_dir} ' + ' '.join(localTag.metadata['urls'])}
    taskName = yield www_tags.realizePhantom('localhost',
                                             request.body['dst_cluster'],
                                             request.body['user_name'],
                                             localTag.tagName,
                                             fakePhantom,
                                             func.updateDict(localTag.metadata, {'urls_realized': True}))
    localTask = yield tasks_tx.loadTask(request.body['task_name'])
    endState, tsk = yield tasks_tx.blockOnTaskAndForward('localhost',
                                                         request.body['dst_cluster'],
                                                         taskName,
                                                         localTask)

    if endState == tasks_tx.task.TASK_FAILED:
        yield tasks_tx.updateTask(request.body['task_name'],
                                  lambda t : t.setState(tasks_tx.task.TASK_FAILED))
        raise RealizePhantomError(request.body['tag_name'])


    if request.body['dst_cluster'] == 'local':
        yield tag_mq_data.tagData(request.state,
                                  request.body['tag_name'],
                                  request.body['task_name'],
                                  files=localTag.files,
                                  action=tag_mq_data.ACTION_APPEND,
                                  metadata={},
                                  recursive=False,
                                  expand=False,
                                  compressDir=None)
    else:
        localTask = yield www_tags.tagData('localhost',
                                           request.body['dst_cluster'],
                                           request.body['user_name'],
                                           action=tag_mq_data.ACTION_APPEND,
                                           tagName=localTag.tagName,
                                           files=localTag.files,
                                           metadata={},
                                           recursive=False,
                                           expand=False,
                                           compressDir=None)

    localTask = yield tasks_tx.loadTask(request.body['task_name'])
    endState, tsk = yield tasks_tx.blockOnTaskAndForward('localhost',
                                                         request.body['dst_cluster'],
                                                         taskName,
                                                         localTask)

    if endState == tasks_tx.task.TASK_FAILED:
        yield tasks_tx.updateTask(request.body['task_name'],
                                  lambda t : t.setState(tasks_tx.task.TASK_FAILED))
        raise RealizePhantomError(request.body['tag_name'])
    
    # Load the tag up and return it so we can have the files it created
    tag = yield www_tags.loadTag('localhost',
                                 request.body['dst_cluster'],
                                 request.body['user_name'],
                                 request.body['tag_name'])

    defer.returnValue(tag)
    
@defer.inlineCallbacks
def _uploadTag(request):
    localTag = yield request.state.tagPersist.loadTag(request.body['tag_name'])

    srcClusters = yield www_clusters.listClusters('localhost',
                                                  {'cluster_name': request.body['src_cluster']},
                                                  request.body['user_name'])

    srcCluster = srcClusters[0]

    dstClusters = yield www_clusters.listClusters('localhost',
                                                  {'cluster_name': request.body['dst_cluster']},
                                                  request.body['user_name'])

    dstCluster = dstClusters[0]

    # We want the trailing '/' so everyone knows it's a directory
    dstTagPath = os.path.join(dstCluster['config']['dirs.upload_dir'], localTag.tagName) + '/'

    # Change dstTagPath to use /mnt/nostaging instead of mnt/staging as the destination if the 
    # tag has a nostaging metadata value
    #if localTag.metadata['nostaging']:
    #    dstTagPath = os.path.join(dstCluster['config']['dirs.nostaging_upload_dir'], localTag.tagName) + '/'
    if request.body['dst_type'] == 'local' :
        upload_dir = '/mnt/nostaging/'
        if 'dirs.nostaging_upload_dir' in dstCluster['config']:
            upload_dir = dstCluster['config']['dirs.nostaging_upload_dir']
        yield _makeDirsOnCluster(dstCluster, [upload_dir])
        dstTagPath = os.path.join(upload_dir, localTag.tagName) + '/'

    baseDirFiles, nonBaseDirFiles = _partitionFiles(localTag.files, localTag.metadata['tag_base_dir'])

    if baseDirFiles:
        yield rsync.rsyncTo(dstCluster['master']['public_dns'],
                            localTag.metadata['tag_base_dir'],
                            dstTagPath,
                            baseDirFiles,
                            srcCluster['config']['rsync.options'],
                            srcCluster['config']['rsync.user'],
                            log=True)

    if nonBaseDirFiles:
        yield rsync.rsyncTo(dstCluster['master']['public_dns'],
                            '/',
                            dstTagPath,
                            nonBaseDirFiles,
                            srcCluster['config']['rsync.options'],
                            srcCluster['config']['rsync.user'],
                            log=True)

    remoteFiles = ([os.path.join(dstTagPath, f) for f in baseDirFiles] +
                   [os.path.join(dstTagPath, _makePathRelative(f)) for f in nonBaseDirFiles])

    metadata = localTag.metadata
    if metadata.get('urls', []) and not metadata.get('urls_realized', False):
        tag = yield _realizeUrls(request)
        remoteFiles.extend(tag['files'])
        metadata = func.updateDict(metadata,
                                   {'urls_realized': True})


    # If we are dealing with an adhoc cluster here there is a chance that
    # we are attempting to transfer to a local VM's shared folder which does 
    # support chown/chmod so we will skip this step
    if dstCluster['master']['instance_type'] is not None:
        yield ssh.runProcessSSH(dstCluster['master']['public_dns'],
                                'chown -R %s %s' % (dstCluster['config']['vappio.user'],
                                                    dstTagPath),
                                None,
                                log.err,
                                srcCluster['config']['ssh.user'],
                                srcCluster['config']['ssh.options'])
        
    defer.returnValue(persist.Tag(tagName=localTag.tagName,
                                  files=remoteFiles,
                                  metadata=func.updateDict(metadata,
                                                           {'tag_base_dir': dstTagPath}),
                                  phantom=localTag.phantom,
                                  taskName=None))


@defer.inlineCallbacks
def _downloadTag(request):
    remoteTag = yield www_tags.loadTag('localhost',
                                       request.body['src_cluster'],
                                       request.body['user_name'],
                                       request.body['tag_name'])

    srcClusters = yield www_clusters.listClusters('localhost',
                                                  {'cluster_name': request.body['src_cluster']},
                                                  request.body['user_name'])

    srcCluster = srcClusters[0]
    
    dstClusters = yield www_clusters.listClusters('localhost',
                                                  {'cluster_name': request.body['dst_cluster']},
                                                  request.body['user_name'])

    dstCluster = dstClusters[0]

    dstTagPath = os.path.join(dstCluster['config']['dirs.upload_dir'], remoteTag['tag_name'])

    baseDirFiles, nonBaseDirFiles = _partitionFiles(remoteTag['files'], remoteTag['metadata']['tag_base_dir'])


    if baseDirFiles:
        yield rsync.rsyncFrom(srcCluster['master']['public_dns'],
                              remoteTag['metadata']['tag_base_dir'],
                              dstTagPath,
                              baseDirFiles,
                              dstCluster['config']['rsync.options'],
                              dstCluster['config']['rsync.user'],
                              log=True)

    if nonBaseDirFiles:
        yield rsync.rsyncFrom(srcCluster['master']['public_dns'],
                              '/',
                              dstTagPath,
                              nonBaseDirFiles,
                              dstCluster['config']['rsync.options'],
                              dstCluster['config']['rsync.user'],
                              log=True)

    remoteFiles = ([os.path.join(dstTagPath, f) for f in baseDirFiles] +
                   [os.path.join(dstTagPath, _makePathRelative(f)) for f in nonBaseDirFiles])
    
    defer.returnValue(persist.Tag(tagName=remoteTag['tag_name'],
                                  files=remoteFiles,
                                  metadata=func.updateDict(remoteTag['metadata'],
                                                           {'tag_base_dir': dstTagPath}),
                                  phantom=remoteTag['phantom'],
                                  taskName=None))

@defer_utils.timeIt    
@defer.inlineCallbacks
def _handleTransferTag(request):
    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.setState(tasks_tx.task.TASK_RUNNING).update(numTasks=2))

    srcTag = yield www_tags.loadTag('localhost',
                                    request.body['src_cluster'],
                                    request.body['user_name'],
                                    request.body['tag_name'])

    if not srcTag['phantom'] and (request.body['src_cluster'] != 'local' or request.body['dst_cluster'] != 'local'):
        if request.body['src_cluster'] == 'local':
            tag = yield _uploadTag(request)
        elif request.body['dst_cluster'] == 'local':
            tag = yield _downloadTag(request)
        else:
            raise NoLocalClusterError('Source cluster or destination cluster must be local')

        yield tasks_tx.updateTask(request.body['task_name'],
                                  lambda t : t.progress())

        if request.body.get('compress', False) or request.body.get('compress_dir', False):
            defaultDir = '/mnt/output' if request.body['dst_cluster'] == 'local' else tag.metadata['tag_base_dir']
            compressDir = request.body.get('compress_dir') if request.body.get('compress_dir', False) else defaultDir 
        else:
            compressDir = None
        
        if request.body['dst_cluster'] == 'local':
            yield tag_mq_data.tagData(request.state,
                                      request.body['tag_name'],
                                      request.body['task_name'],
                                      files=tag.files,
                                      action=tag_mq_data.ACTION_OVERWRITE,
                                      metadata=tag.metadata,
                                      recursive=False,
                                      expand=False,
                                      compressDir=compressDir)
        else:
            newTag = yield www_tags.tagData('localhost',
                                            request.body['dst_cluster'],
                                            request.body['user_name'],
                                            action=tag_mq_data.ACTION_OVERWRITE,
                                            tagName=tag.tagName,
                                            files=tag.files,
                                            metadata=tag.metadata,
                                            recursive=False,
                                            expand=False,
                                            compressDir=compressDir)

            localTask = yield tasks_tx.loadTask(request.body['task_name'])
            endState, tsk = yield tasks_tx.blockOnTaskAndForward('localhost',
                                                                 request.body['dst_cluster'],
                                                                 newTag['task_name'],
                                                                 localTask)
            if endState == tasks_tx.task.TASK_FAILED:
                yield tasks_tx.updateTask(request.body['task_name'],
                                          lambda t : t.setState(tasks_tx.task.TASK_FAILED))
                raise TransferTagError(request.body['tag_name'])
    
        yield tasks_tx.updateTask(request.body['task_name'],
                                  lambda t : t.progress())
    elif not srcTag['phantom'] and srcTag['metadata'].get('urls', []) and not srcTag['metadata'].get('urls_realized', False):
        # It's a local to local but we have urls and haven't realized them
        yield _realizeUrls(request)
        yield tasks_tx.updateTask(request.body['task_name'],
                                  lambda t : t.progress(2))
    elif srcTag['phantom']:
        # Upload the depends file
        srcClusters = yield www_clusters.listClusters('localhost',
                                                      {'cluster_name': request.body['src_cluster']},
                                                      request.body['user_name'])

        srcCluster = srcClusters[0]
        
        dstClusters = yield www_clusters.listClusters('localhost',
                                                      {'cluster_name': request.body['dst_cluster']},
                                                      request.body['user_name'])

        dstCluster = dstClusters[0]
        
        dependsOn = srcTag['phantom'].get('depends_on', '').split()
        yield rsync.rsyncTo(dstCluster['master']['public_dns'],
                            '/',
                            '/',
                            dependsOn,
                            srcCluster['config']['rsync.options'],
                            srcCluster['config']['rsync.user'],
                            log=True)
        
        
        taskName = yield www_tags.realizePhantom('localhost',
                                                 request.body['dst_cluster'],
                                                 request.body['user_name'],
                                                 srcTag['tag_name'],
                                                 srcTag['phantom'],
                                                 srcTag['metadata'])
        localTask = yield tasks_tx.loadTask(request.body['task_name'])
        endState, tsk = yield tasks_tx.blockOnTaskAndForward('localhost',
                                                             request.body['dst_cluster'],
                                                             taskName,
                                                             localTask)
        if endState == tasks_tx.task.TASK_FAILED:
            yield tasks_tx.updateTask(request.body['task_name'],
                                      lambda t : t.setState(tasks_tx.task.TASK_FAILED))
            raise RealizePhantomError(request.body['tag_name'])
        yield tasks_tx.updateTask(request.body['task_name'],
                                  lambda t : t.update(numTasks=1).progress())
    else:
        yield tag_mq_data.tagData(request.state,
                                  request.body['tag_name'],
                                  request.body['task_name'],
                                  files=[],
                                  action=tag_mq_data.ACTION_APPEND,
                                  metadata={},
                                  recursive=False,
                                  expand=False,
                                  compressDir='/mnt/output' if request.body.get('compress', False) else None)
        
        yield tasks_tx.updateTask(request.body['task_name'],
                                  lambda t : t.progress(2))
        
    defer.returnValue(request)

def handleTransferTag(request):
    lock = request.state.tagLocks.setdefault((request.body['cluster'], request.body['tag_name']),
                                             defer.DeferredLock())    
    return lock.run(_handleTransferTag, request)

def _forwardToCluster(conf, queueUrl):
    return queue.forwardRequestToCluster(conf('www.url_prefix') + '/' + os.path.basename(queueUrl))

def subscribe(mq, state):
    processTransferTag = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                 'user_name',
                                                                                 'tag_name',
                                                                                 'src_cluster',
                                                                                 'dst_cluster',
                                                                                 'dst_type']),
                                                               _forwardToCluster(state.conf,
                                                                                 state.conf('tags.transfer_www')),
                                                               queue.createTaskAndForward(state.conf('tags.transfer_queue'),
                                                                                          'transferTag',
                                                                                          0)]))

    queue.subscribe(mq,
                    state.conf('tags.transfer_www'),
                    state.conf('tags.concurrent_transfer'),
                    queue.wrapRequestHandler(state, processTransferTag))

    queue.subscribe(mq,
                    state.conf('tags.transfer_queue'),
                    state.conf('tags.concurrent_transfer'),
                    queue.wrapRequestHandlerTask(state, handleTransferTag))
                                                             

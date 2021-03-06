import os
import StringIO

from twisted.python import log

from twisted.internet import defer

from igs.utils import functional as func

from igs_tx.utils import defer_utils
from igs_tx.utils import defer_pipe
from igs_tx.utils import commands

from vappio_tx.utils import queue

from vappio_tx.tags import persist

from vappio_tx.tasks import tasks as tasks_tx

ACTION_APPEND = 'append'
ACTION_OVERWRITE = 'overwrite'
ACTION_CREATE = 'create'


RESTRICTED_DIRS = ['/bin/',
                   '/boot/',
                   '/dev/',
                   '/etc/',
                   '/home/',
                   '/lib/',
                   '/mnt/keys/',
                   '/mnt/vappio-conf/',
                   '/mnt/user-scripts/',
                   '/opt/',
                   '/proc/',
                   '/root/',
                   '/sbin/',
                   '/tmp/'
                   '/usr/',
                   '/var/',
                   ]

class Error(Exception):
    pass

class TagAlreadyExistsError(Error):
    pass

class UnknownActionError(Error):
    pass

@defer.inlineCallbacks
def _untarFile(fname):
    stdout = StringIO.StringIO()
    yield commands.runProcess(['tar', '-C', os.path.dirname(fname), '-xvf', fname],
                              stdoutf=stdout.write,
                              stderrf=log.err)
    defer.returnValue([str(os.path.join(os.path.dirname(fname), i.strip())) for i in stdout.getvalue().split('\n')])

@defer.inlineCallbacks
def _untargzFile(fname):
    stdout = StringIO.StringIO()
    yield commands.runProcess(['tar', '-C', os.path.dirname(fname), '-zxvf', fname],
                              stdoutf=stdout.write,
                              stderrf=log.err)
    defer.returnValue([str(os.path.join(os.path.dirname(fname), i.strip())) for i in stdout.getvalue().split('\n')])

@defer.inlineCallbacks
def _bunzip2File(fname):
    stdout = StringIO.StringIO()
    yield commands.runProcess(commands.shell('bzcat %s | tar -C %s -xv' % (fname, os.path.dirname(fname))),
                              stdoutf=stdout.write,
                              stderrf=log.err)
    defer.returnValue([str(os.path.join(os.path.dirname(fname), i.strip())) for i in stdout.getvalue().split('\n')])

@defer.inlineCallbacks
def _ungzFile(fname):
    yield commands.runProcess(commands.shell('gzip -dc %s > %s' % (fname, fname[:-3])),
                              stderrf=log.err)
    defer.returnValue(str(fname[:-3]))

@defer.inlineCallbacks
def _unzipFile(fname):
    stdout = StringIO.StringIO()
    yield commands.runProcess(commands.shell('mkdir -p %s && unzip -o -d %s %s' % (os.path.splitext(fname)[0],
                                                                                   os.path.splitext(fname)[0],
                                                                                   fname)),
                              stdoutf=stdout.write,
                              stderrf=log.err)
    log.msg(stdout.getvalue())
    defer.returnValue([str(i.strip().replace('extracting: ', '').replace('inflating: ', '')) for i in stdout.getvalue().split('\n') if ('extracting' in i or 'inflating' in i)])

def _isArchive(fname):
    """
    Returns true if fname ends in:
    .tar
    .tar.bz2
    .tar.gz
    .tgz
    .gz
    .zip
    """
    return any([fname.endswith(i) for i in ['.tar.bz2', '.tar.gz', '.tgz', '.gz', '.tar', '.zip']])


def _expandArchive(fname):
    """
    This expands an archive in the directory the archive lives in and returns the sequence of file names
    """
    if fname.endswith('.tar.gz') or fname.endswith('.tgz'):
        return _untargzFile(fname)
    elif fname.endswith('.gz'):
        return _ungzFile(fname)
    elif fname.endswith('.tar.bz2'):
        return _bunzip2File(fname)
    elif fname.endswith('.tar'):
        return _untarFile(fname)
    elif fname.endswith('.zip'):
        return _unzipFile(fname)

def _generateFileList(files, recursive, expand, deleteOnExpand):
    @defer.inlineCallbacks
    def _(accum, f):
        if expand and _isArchive(f):
            expandedFiles = yield _expandArchive(f)
            if deleteOnExpand:
                os.unlink(f)
            defer.returnValue(accum + [i for i in expandedFiles if os.path.isfile(i) and not '__MACOSX' in i])
        elif recursive and os.path.isdir(f):
            recursedFiles = yield _generateFileList([os.path.join(f, fname)
                                                     for fname in os.listdir(f)],
                                                    recursive,
                                                    expand,
                                                    deleteOnExpand)
            defer.returnValue(accum + recursedFiles)
        elif os.path.isfile(f):
            ## Hacky fix for Mac OSX-created archives that will have dot files in them
            if '__MACOSX' in str(f):
                defer.returnValue(accum)
            else:
                defer.returnValue(accum + [str(f)])
        else:
            raise IOError('%s does not exist' % f)

    return defer_utils.fold(_, [], files)



def _removeBase(baseDir, f):
    if baseDir[-1] != '/':
        baseDir += '/'

    if f.startswith(baseDir):
        return f.replace(baseDir, '', 1)

    return f

def _partitionFiles(files, baseDir):
    if baseDir:
        baseDirFiles = [_removeBase(baseDir, f)
                        for f in files
                        if f.startswith(baseDir)]
        downloadFiles = [f
                         for f in files
                         if not f.startswith(baseDir)]
        return (baseDirFiles, downloadFiles)
    else:
        return ([], files)

@defer.inlineCallbacks
def _compressFiles(tag, compressDir):
    compressedFile = os.path.join(compressDir, tag.tagName + '.tar.gz')

    yield commands.runProcess(['mkdir', '-p', compressDir], stderrf=log.err)
    
    baseDirFiles, nonBaseDirFiles = _partitionFiles(tag.files, tag.metadata['tag_base_dir'])

    cmd = ['tar',
           '-C', tag.metadata['tag_base_dir'],
           '-czhf', compressedFile,
           '--files-from=-']

    yield commands.runProcess(cmd,
                              stderrf=log.err,
                              initialText=str('\n'.join(baseDirFiles + nonBaseDirFiles)))
    defer.returnValue(compressedFile)
    
@defer.inlineCallbacks
def tagData(state, tagName, taskName, files, metadata, action, recursive, expand, compressDir, filterF=None, deleteOnExpand=False):
    if not os.path.exists(state.conf('tags.tags_directory')):
        yield commands.runProcess(['mkdir', '-p', state.conf('tags.tags_directory')])

    files = yield _generateFileList(files, recursive, expand, deleteOnExpand)

    if action == ACTION_APPEND:
        try:
            tag = yield state.tagPersist.loadTag(tagName)
            metadata = func.updateDict(tag.metadata, metadata)
            oldFiles = set(tag.files)
        except persist.TagNotFoundError:
            oldFiles = set()
    else:
        oldFiles = set()

    if 'tag_base_dir' not in metadata:
        metadata['tag_base_dir'] = '/'
    files = [f
             for f in files
             if f not in oldFiles and (not filterF or filterF and filterF(f))]

    files += oldFiles

    # Remove any dups
    files = list(set(files))
    
    tag = persist.Tag(tagName=tagName,
                      files=files,
                      metadata=metadata,
                      phantom=None,
                      taskName=taskName)
    

    if compressDir:
        compressedFile = yield _compressFiles(tag, compressDir)
        tag.metadata = func.updateDict(tag.metadata,
                                       {'compressed': True,
                                        'compressed_file': compressedFile})
    else:
        tag.metadata = func.updateDict(tag.metadata,
                                       {'compressed': False})

    yield state.tagPersist.saveTag(tag)

    # The tag we saved at phantom set to None, but this could be a
    # phantom tag, in which case we are going to reload it from disk
    # then cache that in order to load any phantom information
    tag = yield state.tagPersist.loadTag(tag.tagName)
    
    defer.returnValue(tag)

def _restrictDirs(f):
    for d in RESTRICTED_DIRS:
        # Special case for Hudson tests
        if f.startswith(d) and not f.startswith('/opt/hudson/'):
            return False

    return True

@defer_utils.timeIt
@defer.inlineCallbacks
def _handleTaskTagData(request):
    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.setState(tasks_tx.task.TASK_RUNNING).update(numTasks=1))

    if 'urls' in request.body and request.body['urls']:
        metadata = func.updateDict(request.body['metadata'],
                                   {'urls': request.body['urls']})
    else:
        metadata = request.body['metadata']
    
    yield tagData(request.state,
                  request.body['tag_name'],
                  request.body['task_name'],
                  request.body.get('files', []),
                  metadata,
                  request.body['action'],
                  request.body.get('recursive', False),
                  request.body.get('expand', False),
                  request.body.get('compress_dir', None),
                  filterF=_restrictDirs)

    yield tasks_tx.updateTask(request.body['task_name'],
                              lambda t : t.progress())
    
    defer.returnValue(request)


def handleTaskTagData(request):
    """
    This is a small wrapper around _handleTaskTagData just to serialize access to
    the tag
    """
    return request.state.tagLocks[('local', request.body['tag_name'])].run(_handleTaskTagData, request)


def _validateAction(request):
    """
    Validates that the action is one of our predefined ones as well being kosher with
    preexisting actions.  It also saves a placeholder for the tag if it does not exist
    already
    """
    @defer.inlineCallbacks
    def _tagExists(conf, tagName):
        try:
            yield request.state.tagPersist.loadTag(tagName)
            defer.returnValue(True)
        except persist.TagNotFoundError:
            defer.returnValue(False)
        
    @defer.inlineCallbacks
    def __validateAction():
        if request.body['action'] not in [ACTION_APPEND, ACTION_OVERWRITE, ACTION_CREATE]:
            raise UnknownActionError(str(request.body['action']))

        tagExists = yield _tagExists(request.state.conf, request.body['tag_name'])
        
        if request.body['action'] == ACTION_CREATE and tagExists:
            raise TagAlreadyExistsError(request.body['tag_name'])

            
        if not tagExists:
            # Save a placeholder for this tag so future queued requests can validate themselves
            # against it
            tag = persist.Tag(request.body['tag_name'],
                              [],
                              {},
                              None,
                              None)
            yield request.state.tagPersist.saveTag(tag)
        defer.returnValue(request)

    lock = request.state.tagLocks.setdefault(('local', request.body['tag_name']),
                                             defer.DeferredLock())
    return lock.run(__validateAction)

def _forwardToCluster(conf, queueUrl):
    return queue.forwardRequestToCluster(conf('www.url_prefix') + '/' + os.path.basename(queueUrl))


def _returnTag(request):
    tag = persist.Tag(request.body['tag_name'],
                      [],
                      {},
                      None,
                      request.body['task_name'])
    return defer_pipe.ret(request.update(response=persist.tagToDict(tag)))

def subscribe(mq, state):
    processTagData = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                             'tag_name',
                                                                             'metadata',
                                                                             'action']),
                                                           _forwardToCluster(state.conf,
                                                                             state.conf('tags.createupdate_www')),
                                                           _validateAction,
                                                           queue.createTaskAndForward(state.conf('tags.createupdate_queue'),
                                                                                      'tagCreateUpdate',
                                                                                      0),
                                                           _returnTag]))
    queue.subscribe(mq,
                    state.conf('tags.createupdate_www'),
                    state.conf('tags.concurrent_createupdate'),
                    queue.wrapRequestHandler(state, processTagData))

    queue.subscribe(mq,
                    state.conf('tags.createupdate_queue'),
                    state.conf('tags.concurrent_createupdate'),
                    queue.wrapRequestHandlerTask(state, handleTaskTagData))

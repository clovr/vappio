import StringIO

from twisted.internet import defer
from twisted.internet import reactor

from igs_tx.utils import defer_pipe

from igs_tx.utils import commands

from vappio_tx.utils import queue

# Every 30 minutes
PATCH_UPDATE_FREQUENCY = 30 * 60

@defer.inlineCallbacks
def _getPatchList(patchUrl, currentMajorVersion, currentPatchVersion):
    yield commands.runProcess(['mkdir', '-p', '/tmp/patches'])

    nextPatchVersion = currentPatchVersion + 1
    nextPatch = '%s-p%d' % (currentMajorVersion, nextPatchVersion)

    try:
        yield commands.runProcess(['svn',
                                   'export',
                                   '%s/%s' % (patchUrl, nextPatch),
                                   '/tmp/patches/%s' % nextPatch],
                                  log=True)
        morePatches = yield _getPatchList(patchUrl, currentMajorVersion, nextPatchVersion)
        defer.returnValue([nextPatch] + morePatches)
    except commands.ProgramRunError:
        defer.returnValue([])


@defer.inlineCallbacks
def _checkForUpdates(state):
    state.patches = yield _getPatchList(state.conf('vm.patch_url'),
                                        state.majorVersion,
                                        state.patchVersion)


@defer.inlineCallbacks
def _checkForUpdatesAndLoop(state):
    yield _checkForUpdates(state)
    reactor.callLater(PATCH_UPDATE_FREQUENCY,
                      _checkForUpdatesAndLoop,
                      state)

    

@defer.inlineCallbacks
def _sharedFoldersEnabled(vmType):
    if vmType == 'vmware':
        stdout = StringIO.StringIO()
        yield commands.runProcess(['df'], stdoutf=stdout.write)
        defer.returnValue('.host:/shared' in stdout.getvalue())
    else:
        defer.returnValue(False)

@defer.inlineCallbacks
def _getVMInfo(state):
    releaseName = open('/etc/vappio/release_name.info').read().strip()

    if state.releaseName and releaseName != state.releaseName:
        state.releaseName = releaseName
        yield _checkForUpdates(state)
    else:
        state.releaseName = releaseName

    versionSplit = state.releaseName.split('-p')
    if len(versionSplit) == 2:
        state.majorVersion = versionSplit[0]
        state.patchVersion = int(versionSplit[1])
    else:
        state.majorVersion = versionSplit[0]
        state.patchVersion = 0
    

    state.vmType = open('/var/vappio/runtime/cloud_type').read().strip()
    state.sharedFoldersEnabled = yield _sharedFoldersEnabled(state.vmType)
    
@defer.inlineCallbacks
def handleWWWInfo(request):
    yield _getVMInfo(request.state)
    
    response = {}
    
    response['release_name'] = request.state.releaseName
    response['major_version'] = request.state.majorVersion
    response['patch_version'] = request.state.patchVersion
    response['patches'] = request.state.patches

    response['vm_type'] = request.state.vmType

    response['shared_folders_enabled'] = request.state.sharedFoldersEnabled

    defer.returnValue(request.update(response=response))

@defer.inlineCallbacks
def subscribe(mq, state):
    print 'MADE IT HERE'
    yield _getVMInfo(state)
    yield _checkForUpdatesAndLoop(state)
    print 'MADE IT THERE'
    
    processInfo = queue.returnResponse(defer_pipe.pipe([handleWWWInfo]))
    queue.subscribe(mq,
                    state.conf('vm.info_www'),
                    state.conf('vm.concurrent_info'),
                    queue.wrapRequestHandler(state, processInfo))

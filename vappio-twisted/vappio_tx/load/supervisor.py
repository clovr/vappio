import os
import StringIO

from twisted.python import log

from twisted.internet import reactor
from twisted.internet import defer

from igs_tx.utils import commands

from vappio_tx.internal_client import clusters_client

EXEC_QUEUE = 'exec.q'
STAGING_QUEUE = 'staging.q'

# Refresh every 60 seconds
REFRESH_FREQUENCY = 60


class MachineInformation:
    def __init__(self):
        self._execSlots = 0
        self._stagingSlots = 0

    def setExecSlots(self, execSlots):
        self._execSlots = execSlots
        return self

    def execSlots(self):
        return self._execSlots

    def setStagingSlots(self, stagingSlots):
        self._stagingSlots = stagingSlots
        return self

    def stagingSlots(self):
        return self._stagingSlots

@defer.inlineCallbacks
def _loopSupervisorNoThrow(state):
    localCluster = yield clusters_client.loadCluster('local', None)
                                                     
    loadAverages = os.getloadavg()

    oneMinuteLoad = loadAverages[0]
    
    if (oneMinuteLoad > 10 and
        state.master.execSlots() > 0 and
        len(localCluster['exec_nodes']) > 0):
        execSlots = state.master.execSlots()
        execSlots -= 1
        yield sge_queue.setSlotsForQueue(EXEC_QUEUE, self.hostname, execSlots)
        state.master.setExecSlots(execSlots)
    elif (oneMinuteLoad < 10 and
          state.master.execSlots() == 0 and
          len(localCluster['exec_nodes']) == 0):
        execSlots = state.master.execSlots()
        execSlots += 1
        yield sge_queue.setSlotsForQueue(EXEC_QUEUE, self.hostname, execSlots)
        state.master.setExecSlots(execSlots)
        


@defer.inlineCallbacks
def _loopSupervisor(state):
    try:
        yield _loopSupervisorNoThrow(state)
    except Exception, err:
        log.err(err)
        
    reactor.callLater(REFRESH_FREQUENCY, _loopSupervisor, state)

    
@defer.inlineCallbacks
def _createSupervisor(state):
    output = yield commands.getOutput(['hostname', '-f'])
    
    self.hostname = output['stdout']
    
    # Let's get our queue information
    execSlots = yield sge_queue.listSlotsForQueue(EXEC_QUEUE)
    stagingSlots = yield sge_queue.listSlotsForQueue(STAGING_QUEUE)
    self.master = MachineInformation().setExecSlots(execSlots['nodes'][hostname]
                                                    ).setStagingSlots(stagingSlots['nodes'][hostname])
    
    reactor.callLater(0.0, _loopSupervisor, state)

def subscribe(_mq, state):
    """
    This doesn't actually subscribe to any queues but this is the standard
    way components register themselves.  This just sets up a loop to check
    things about the machine and adjust them as necessary.
    """
    _createSupervisor(state)
    

import json

from igs.utils import logging

from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

@defer_utils.timeIt
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
    logging.debugPrint(lambda : repr(request.body))
    request.mq.send('/queue/pipelines/observer/' + request.body['props'],
                    json.dumps(request.body))
    return defer_pipe.ret(request.update(response=None))

def subscribe(mq, state):
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
    

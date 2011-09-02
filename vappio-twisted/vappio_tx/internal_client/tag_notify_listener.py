from twisted.internet import defer

from igs.utils import dependency

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

LOAD_TOPIC = '/topic/tags/load'
SAVE_TOPIC = '/topic/tags/save'
REMOVE_TOPIC = '/topic/tags/remove'

def _wrapRequestHandler(f):
    return defer_pipe.pipe([queue.decodeRequest,
                            defer_pipe.hookError(defer_pipe.pipe([f,
                                                                  queue.ackMsg]),
                                                 queue.ackMsgFailure)])
    

class TagNotifyListener(dependency.Dependable):
    def __init__(self):
        dependency.Dependable.__init__(self)

    def initialize(self, mq):
        self.mq = mq

        for topic, func in [(LOAD_TOPIC, self._load),
                            (SAVE_TOPIC, self._save),
                            (REMOVE_TOPIC, self._remove)]:
            queue.subscribe(self.mq,
                            topic,
                            1,
                            _wrapRequestHandler(func))

        return defer.succeed(None)


    def release(self):
        for topic in [LOAD_TOPIC, SAVE_TOPIC, REMOVE_TOPIC]:
            self.mq.unsubscribe(topic)

        return defer.succeed(None)
            
    def _load(self, request):
        self.changed('load', request.body)
        return request

    def _save(self, request):
        self.changed('save', request.body)
        return request

    def _remove(self, request):
        self.changed('remove', request.body)
        return request


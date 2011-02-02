import json

from twisted.python import log
from twisted.python import failure

from twisted.internet import defer

from igs.utils import functional as func

class QueueSubscription(func.Record):
    """
    Represents the subscription to a queue with variables for
    validating the message (.ensureF), function to call on success (.successF),
    function to call on failure (.failureF)
    """

    def __init__(self, ensureF, successF, failureF):
        func.Record.__init__(self,
                             ensureF=ensureF,
                             successF=successF,
                             failureF=failureF)


    def setEnsure(self, ensureF):
        return self.update(ensureF=ensureF)

    def setSuccess(self, successF):
        return self.update(successF=successF)

    def setFailure(self, failureF):
        return self.update(failureF=failureF)

    def __call__(self, mq, msg):
        try:
            body = json.loads(msg.body)
            if not self.ensureF or (self.ensureF and self.ensureF(body)):
                d = defer.succeed(True)
                d.addCallback(lambda _ : self.successF and self.successF(mq, body))

                def _ack(x):
                    mq.ack(msg.headers['message-id'])
                    return x

                d.addCallback(_ack)
                # Consume bad messages regardless
                d.addErrback(_ack)
                d.addErrback(lambda failure : self.failureF and self.failureF(mq, body, failure))

                def _logAndReturn(failure):
                    log.err(failure)
                    return failure

                d.addErrback(_logAndReturn)
            else:
                try:
                    if self.failureF:
                        f = failure.Failure(Exception('Request did not pass verification'))
                        self.failureF(mq, body, f)
                except Exception, err:
                    log.err('failureF call failed')
                    log.err(failure.Failure(err))
                # If it's bad data, ack it and get rid of it and log it
                mq.ack(msg.headers['message-id'])
                log.err('Incoming request failed verification: ' + msg.body)
        except ValueError, err:
            # Incase JSON is invalid
            mq.ack(msg.headers['message-id'])
            log.err('Incoming request failed to decode from json: ' + msg.body)
            log.err(err)

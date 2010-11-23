import json

from vappio_tx.utils import queue
from vappio_tx.tasks import tasks

def createTaskAndForward(mq, destQueue, tType, numTasks, verifierF):
    """
    Creates a queue handler function that will read values off a queue
    and ack them and call verifierF on the body.  If the verification is valid
    then a task is created and added to the request and send to destQueue.

    It is assumed that the value read off originQueue is a JSON dictionary
    """

    def _handler(msg):
        data = json.loads(msg.body)
        try:
            if verifierF(data):
                d = tasks.createTaskAndSave(tType, numTasks)

                def _forward(taskName):
                    data['task_name'] = taskName
                    mq.send(destQueue, json.dumps(data))
                    mq.ack(msg.headers['message-id'])
                    queue.returnQueueSuccess(mq, data['return_queue'], taskName)

                def _error(f):
                    mq.ack(msg.headers['message-id'])
                    queue.returnQueueFailure(mq, data['return_queue'], f)
                    return f
                            
                d.addCallback(_forward)
                d.addErrback(_error)
            else:
                queue.returnQueueError(mq, data['return_queue'], 'Data did not pass verifier: ' + msg.body)
        except:
            queue.returnQueueException(mq, data['return_queue'])

    return _handler

            

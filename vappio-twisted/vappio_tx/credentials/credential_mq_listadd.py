import os

from twisted.internet import defer

from twisted.python import log

from igs.utils import core
from igs.utils import config

from igs_tx.utils import defer_pipe
from igs_tx.utils import defer_utils

from vappio_tx.utils import queue

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.credentials import persist



class Error(Exception):
    pass

class UnknownRequestError(Error):
    pass        


@defer_utils.timeIt
@defer.inlineCallbacks
def instantiateAndSaveCredential(taskName, cred, credentialPersist):
    """
    Make sure that the credential can be loaded, otherwise chuck it
    """
    try:
        yield cred.ctype.instantiateCredential(cred.conf, cred)
        yield credentialPersist.saveCredential(cred)
        yield tasks_tx.updateTask(taskName,
                                  lambda t : t.setState(tasks_tx.task.TASK_COMPLETED).progress())
    except Exception, err:
        log.err('Error loading credential')
        log.err(err)
        yield tasks_tx.updateTask(taskName,
                                  lambda t : t.setState(tasks_tx.task.TASK_FAILED))

@defer_utils.timeIt
@defer.inlineCallbacks
def handleWWWListAddCredentials(request):

    if 'credential_name' in request.body and core.keysInDict(['credential_name',
                                                              'description',
                                                              'ctype',
                                                              'metadata'],
                                                            request.body):
        # Users can provide a file name or the actual contents of the
        # certificate.
        if 'cert_file' in request.body:
            cert = open(request.body['cert_file']).read()
        else:
            cert = request.body['cert']

        if 'pkey_file' in request.body:
            pkey = open(request.body['pkey_file']).read()
        else:
            pkey = request.body['pkey']

        conf = config.configFromMap(request.body.get('conf', {}),
                                    base=config.configFromEnv())
        cred = persist.createCredential(name=request.body['credential_name'],
                                        desc=request.body['description'],
                                        ctype=request.body['ctype'],
                                        cert=cert,
                                        pkey=pkey,
                                        active=True,
                                        metadata=request.body['metadata'],
                                        conf=conf)

        taskName = yield tasks_tx.createTaskAndSave('addCredential', 1)

        instantiateAndSaveCredential(taskName, cred, request.state.credentialPersist)

        queue.returnQueueSuccess(request.mq,
                                 request.body['return_queue'],
                                 taskName)
        defer.returnValue(request)                                       
    elif 'credential_name' not in request.body:
        credentials = request.state.credentialsCache.getAllCredentials()

        credentialsDicts = [{'name': name,
                             'description': c['cred_instance'].credential.desc,
                             'num_instances': len(c['instances']),
                             'ctype': c['cred_instance'].credential.getCType()}
                             for name, c in credentials.iteritems()
                             if ('credential_names' in request.body and name in request.body['credential_names']) or
                             'credential_names' not in request.body]

        
        queue.returnQueueSuccess(request.mq,
                                 request.body['return_queue'],
                                 credentialsDicts)

        defer.returnValue(request)
    else:
        queue.returnQueueError(request.mq,
                               request.body['return_queue'],
                               'Unknown credential query')        
        
        raise UnknownRequestError(str(request.body))

def subscribe(mq, state):
    processWWWListAddCredentials = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['cluster']),
                                                                         queue.forwardRequestToCluster(
                                                                             state.conf('www.url_prefix') + '/' +
                                                                             os.path.basename(state.conf('credentials.listaddcredentials_www'))),
                                                                         handleWWWListAddCredentials]),
                                                        queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.listaddcredentials_www'),
                    state.conf('credentials.concurrent_listaddcredentials'),
                    queue.wrapRequestHandler(state, processWWWListAddCredentials))

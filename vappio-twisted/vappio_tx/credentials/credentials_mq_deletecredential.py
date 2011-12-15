import os

from twisted.internet import defer

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue
from vappio_tx.www_client import clusters as clusters_client

class Error(Exception):
    pass

class CredentialInUseError(Error):
    pass    

@defer.inlineCallbacks
def handleWWWDeleteCredential(request):
    clusters = yield clusters_client.listClusters('localhost',
                                                  'local',
                                                  'guest')

    for cluster in clusters:
        if cluster['cred_name'] == request.body['credential_name']:
            raise CredentialInUseError()

    if not request.body.get('dry_run', False):
        yield request.state.credentialPersist.deleteCredential(request.body['credential_name'])

    queue.returnQueueSuccess(request.mq,
                             request.body['return_queue'],
                             True)

    defer.returnValue(request)

def subscribe(mq, state):
    processWWWDeleteCredential = defer_pipe.hookError(defer_pipe.pipe([queue.keysInBody(['credential_name']),
                                                                       queue.forwardRequestToCluster(
                                                                           state.conf('www.url_prefix') + '/' +
                                                                            os.path.basename(state.conf('credentials.delete_www'))),
                                                                       handleWWWDeleteCredential]),
                                                      queue.failureMsg)
    queue.subscribe(mq,
                    state.conf('credentials.delete_www'),
                    state.conf('credentials.concurrent_deletecredential'),
                    queue.wrapRequestHandler(state, processWWWDeleteCredential))

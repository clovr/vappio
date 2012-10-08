from twisted.internet import defer
from twisted.internet import reactor
from twisted.internet import error

from twisted.python import log

from igs.utils import errors
from igs.utils import auth_token

from igs_tx.utils import defer_utils
from igs_tx.utils import ssh
from igs_tx.utils import commands

from vappio_tx.www_client import clusters as clusters_www_client

CLUSTER_REFRESH_FREQUENCY = 30

@defer_utils.timeIt
@defer.inlineCallbacks
def loadRemoteCluster(state, cl):
    """
    Tries to load a cluster.  Returns the cluster on success
    otherwise throws an error.

    If the cluster is not actually owned by us throws
    auth_token.AuthTokenError

    If it's unresponsive throws
    errors.RemoteError

    We also check for SSH being up and throw a RemoteError
    if it is not responsive
    """
    if cl.master:
        authToken = auth_token.generateToken(cl.config('cluster.cluster_public_key'))

        try:
            clusters = yield clusters_www_client.listClusters(cl.master['public_dns'],
                                                              {'cluster_name': 'local'},
                                                              None,
                                                              authToken,
                                                              timeout=10,
                                                              tries=3)

            cluster = clusters[0]

            yield ssh.runProcessSSH(cl.master['public_dns'],
                                    'echo hello',
                                    stdoutf=None,
                                    stderrf=None,
                                    sshUser=state.machineConf('ssh.user'),
                                    sshFlags=state.machineConf('ssh.options'))

            defer.returnValue(cluster)
        except errors.RemoteError, err:
            if err.name == 'igs.utils.auth_token.AuthTokenError':
                raise auth_token.AuthTokenError()
            else:
                raise
        except commands.ProgramRunError:
            raise errors.RemoteError('SSH failed')
        except error.TimeoutError:
            raise errors.RemoteError('Timeout')
        

@defer.inlineCallbacks
def refreshClusters(mq, state):
    persistManager = state.persistManager

    try:
        clusters = yield persistManager.loadClustersByAdmin({})

        for cluster in clusters:
            try:
                if cluster.state in [cluster.RUNNING, cluster.UNRESPONSIVE]:
                    remoteCluster = yield loadRemoteCluster(state, cluster)

                    cluster = cluster.addExecNodes(remoteCluster['exec_nodes'])
                    cluster = cluster.addDataNodes(remoteCluster['data_nodes'])
                    cluster = cluster.updateExecNodes(remoteCluster['exec_nodes'])
                    cluster = cluster.updateDataNodes(remoteCluster['data_nodes'])
                    cluster = cluster.setState(cluster.RUNNING)

                    yield persistManager.saveCluster(cluster)
            except auth_token.AuthTokenError:
                ## If we got an auth token error it means that
                ## a cluster we thought we owned isn't actually
                ## owned by us.  Let's log this information out
                ## and then remove it from our list.
                log.msg('AUTH_TOKEN_ERROR: Cluster: %s Master: %s' % (
                        cluster.clusterName,
                        cluster.master['public_dns']))
                yield persistManager.removeCluster(cluster.clusterName,
                                                   cluster.userName)
            except Exception, err:
                log.msg('REFRESH: Error')
                log.err(err)
                currCluster = yield persistManager.loadCluster(cluster.clusterName,
                                                               cluster.userName)

                ## The state of the cluster could have changed since
                ## we tried to access it
                if currCluster.state in [cluster.RUNNING, cluster.UNRESPONSIVE]:
                    cluster = cluster.setState(cluster.UNRESPONSIVE)
                    yield persistManager.saveCluster(cluster)

    except Exception, err:
        ## Incase anything goes wrong, try again
        log.msg('REFRESH: Error')
        log.err(err)
        
    reactor.callLater(CLUSTER_REFRESH_FREQUENCY, refreshClusters, mq, state)


def subscribe(mq, state):
    refreshClusters(mq, state)
    

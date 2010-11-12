#!/usr/bin/env python
##
# This adds instances to the current cluster.  This should run on the master node of
# whatever cluster instances are being added to
from igs.utils import cli
from igs.utils.config import configFromMap
from igs.utils import functional as func
from igs.utils import errors

from vappio.core.error_handler import runCatchError, mongoFail

from vappio.cluster.control import Cluster
from vappio.cluster import control as cluster_ctl
from vappio.cluster import persist_mongo

from vappio.webservice import cluster

from vappio.tasks import task
from vappio.tasks import utils as task_utils

from vappio.credentials import manager
from vappio.credentials import persist as cred_persist

OPTIONS = [
    ('name', '', '--name', 'Name of the cluster', cli.notNone),
    ('task_name', '', '--task-name', 'Name of task associated with this', cli.notNone),
    ('cred', '', '--cred', 'Credentials to use', cli.notNone),
    ('num', '', '--num', 'Number of nodes to create', func.compose(int, cli.notNone)),
    ('update_dirs', '', '--update_dirs', 'Update scritps directories', cli.defaultIfNone(False), True),
    ]

def updateCluster(cl):
    """
    This keeps on setting the cluster master to the new value and
    dumping it to the database
    """
    try:
        dbCluster = cluster_ctl.loadCluster(cl.name)
        cl = cl.addExecNodes(dbCluster.execNodes).addDataNodes(dbCluster.dataNodes)
    except persist_mongo.ClusterDoesNotExist:
        pass
    except persist_mongo.ClusterLoadIncompleteError:
        pass

    cluster_ctl.saveCluster(cl)
    


def addExecInstances(options, cl, tsk):
    ##
    # If there are other instances to be added then start them
    # and forward any messages onto the current task
    # if adding them fails, then throw an TryError
    # with 

    try:
        taskName = cluster.addInstances('localhost',
                                        options('general.name'),
                                        options('general.num'),
                                        options('general.update_dirs'))
        endState, tsk = task_utils.blockOnTaskAndForward('localhost',
                                                         options('general.name'),
                                                         taskName,
                                                         tsk)
    except errors.TryError, err:
        raise Exception('Failed to add exec instances: ' + str(err))
    
    if endState == task.TASK_FAILED:
        raise errors.TryError('Failed to add instances to cluster', cl)

    return tsk, cl


def clusterExists(host, name):
    try:
        cluster.loadCluster(host, name)
        return True
    except errors.TryError:
        return False

    
def main(options, _args):
    options = configFromMap(
        {'cluster': {'master_groups': [f.strip() for f in options('cluster.master_groups').split(',')],
                     'exec_groups': [f.strip() for f in options('cluster.exec_groups').split(',')],
                     }
         }, options)

    tsk = task.updateTask(task.loadTask(options('general.task_name')
                                        ).setState(task.TASK_RUNNING
                                                   ).addMessage(task.MSG_SILENT, 'Starting master'))

    try:
        tsk = task.updateTask(tsk.addMessage(task.MSG_NOTIFICATION, 'Loading credential...'))
        cred = manager.loadCredential(options('general.cred'))
    except cred_persist.CredentialDoesNotExistError, err:
        tsk = task.updateTask(tsk.setState(task.TASK_FAILED).addException('Credential does not exist: ' + options('general.cred'), err, errors.getStacktrace()))
        raise
        

    # Try to load the cluster.  If it does not exist, continue and make it, if it does exist noop
    if not clusterExists('localhost', options('general.name')):
        cl = Cluster(options('general.name'), cred, options)
        try:
            cl = cl.startMaster(updateCluster)
            
            updateCluster(cl)

            tsk = task.updateTask(tsk.progress())
            
            if options('general.num'):
                tsk, cl = addExecInstances(options, cl, tsk)

            tsk = tsk.progress().setState(task.TASK_COMPLETED)
        except errors.TryError, err:
            tsk = tsk.setState(task.TASK_COMPLETED).addException('An error occured attempting to start the cluster:\n' + err.msg +
                                                                 '\nThe cluster has been started as much as possible, it may not function properly though',
                                                                 err,
                                                                 errors.getStacktrace())
            # err.result should be the cluster in this case
            updateCluster(err.result)
    else:
        tsk = tsk.setState(task.TASK_COMPLETED).addMessage(task.MSG_NOTIFICATION, 'Cluster already running')
    
    tsk = task.updateTask(tsk)
        
if __name__ == '__main__':
    runCatchError(lambda : task_utils.runTaskMain(main,
                                                  *cli.buildConfigN(OPTIONS)),
                  mongoFail(dict(action='startCluster')))

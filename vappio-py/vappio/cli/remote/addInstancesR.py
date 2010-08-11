#!/usr/bin/env python
##
# This adds instances to the current cluster.  This should run on the master node of
# whatever cluster instances are being added to
from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.functional import compose
from igs.utils import errors

from vappio.core.error_handler import runCatchError, mongoFail
from vappio.cluster import control as cluster_ctl
from vappio.cluster import persist_mongo

from vappio.tasks import task

OPTIONS = [
    ('task_name', '', '--task-name', 'Name of task', notNone),
    ('num', '', '--num', 'Number of nodes to create', compose(int, notNone)),
    ('update_dirs', '', '--update_dirs', 'Update scritps directories', defaultIfNone(False), True),
    ]


def updateCluster(cl):
    """
    This keeps on setting the cluster master to the new value and
    dumping it to the database
    """
    try:
        dbCluster = cluster_ctl.loadCluster(cl.name)
        cl = cl.addExecNodes(dbCluster.addExecNodes(cl.execNodes).execNodes
                             ).addDataNodes(dbCluster.addDataNodes(cl.dataNodes).dataNodes)
    except persist_mongo.ClusterDoesNotExist:
        pass

    cluster_ctl.saveCluster(cl)


    
def main(options, _args):

    tsk = task.updateTask(task.loadTask(options('general.task_name')
                                        ).setState(task.TASK_RUNNING
                                                   ).addMessage(task.MSG_SILENT, 'Starting instances'))

    try:
        cluster = cluster_ctl.loadCluster('local').startExecNodes(options('general.num'), updateCluster)
        tsk = tsk.progress().setState(task.TASK_COMPLETED)
        updateCluster(cluster)
    except errors.TryError, err:
        tsk = tsk.setState(task.TASK_COMPLETED).addException('An error occured attempting to start the instances: ' + err.msg +
                                                             '\nThe cluster has been started as much as possible, it may not function properly though',
                                                             err,
                                                             errors.getStacktrace())
        updateCluster(err.result)
    except Exception, err:
        tsk = task.updateTask(tsk.setState(task.TASK_FAILED
                                           ).addMessage(task.MSG_ERROR,
                                                        'An error occured attempting to start the cluster:\n' + str(err) + '\nExiting...'))
        raise

    tsk = task.updateTask(tsk)        
    

if __name__ == '__main__':
    runCatchError(lambda : main(*buildConfigN(OPTIONS)),
                  mongoFail(dict(action='addInstances')))

#!/usr/bin/env python
##
# This adds instances to the current cluster.  This should run on the master node of
# whatever cluster instances are being added to
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.config import configFromEnv, configFromStream, configFromMap
from igs.utils.logging import logPrint, debugPrint
from igs.utils.functional import compose
from igs.utils.commands import runSingleProgramEx

from vappio.core.error_handler import runCatchError, mongoFail
from vappio.cluster.misc import getInstances
from vappio.cluster.control import Cluster, startExecNodes
from vappio.cluster.persist_mongo import load, dump, ClusterDoesNotExist

from vappio.tasks import task

from vappio.ec2 import control as ec2control

OPTIONS = [
    ('task_name', '', '--task-name', 'Name of task', notNone),
    ('num', '', '--num', 'Number of nodes to create', compose(int, notNone)),
    ('update_dirs', '', '--update_dirs', 'Update scritps directories', defaultIfNone(False), True),
    ]



def updateExecCluster(cluster, instances):
    """
    This keeps on setting the cluster master to the new value and
    dumping it to the database
    """
    #debugPrint(lambda : 'Updating cluster: %s %s' % (master.publicDNS, master.state))
    insts = dict([(i.instanceId, i) for i in cluster.execNodes])
    insts.update(dict([(i.instanceId, i) for i in instances]))
    cluster.execNodes = insts.values()
    cluster.addExecNodes(instances)
    dump(cluster)


def main(options, _args):
    cluster = load('local')

    tsk = task.updateTask(task.loadTask(options('general.task_name')
                                        ).setState(task.TASK_RUNNING
                                                   ).addMessage(task.MSG_SILENT, 'Starting instances'))

    try:
        startExecNodes(cluster, options('general.num'), lambda i : updateExecCluster(cluster, i))
        tsk = tsk.progress().setState(task.TASK_COMPLETED)
        dump(cluster)
    except TryError, err:
        tsk = tsk.setState(task.TASK_COMPLETED).addMessage(task.MSG_ERROR, 'An error occured attempting to start the instances:\n' + err.msg +
                                                           '\nThe cluster has been started as much as possible')
        dump(err.result)
    except Exception, err:
        tsk = task.updateTask(tsk.setState(task.TASK_FAILED
                                           ).addMessage(task.MSG_ERROR,
                                                        'An error occured attempting to start the cluster:\n' + str(err) + '\nExiting...'))
        raise

    tsk = task.updateTask(tsk)        
    

    
if __name__ == '__main__':
    runCatchError(lambda : main(*buildConfigN(OPTIONS)),
                  mongoFail(dict(action='addInstances')))

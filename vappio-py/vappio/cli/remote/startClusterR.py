#!/usr/bin/env python
##
# This adds instances to the current cluster.  This should run on the master node of
# whatever cluster instances are being added to
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone, restrictValues
from igs.utils.config import configFromMap
from igs.utils.logging import logPrint, errorPrint, debugPrint
from igs.utils.functional import compose
from igs.utils.commands import runSingleProgramEx
from igs.utils.errors import TryError

from vappio.core.error_handler import runCatchError, mongoFail

from vappio.cluster.control import Cluster, startMaster
from vappio.cluster.persist_mongo import dump

from vappio.webservice.cluster import addInstances

from vappio.tasks import task
from vappio.tasks.utils import blockOnTaskAndForward

from vappio.ec2 import control as ec2control

OPTIONS = [
    ('conf', '', '--conf', 'Name of config file to use', compose(lambda x : '${env.VAPPIO_HOME}/vappio-conf/' + x, notNone)),
    ('name', '', '--name', 'Name of the cluster', notNone),
    ('task_name', '', '--task-name', 'Name of task associated with this', notNone),
    ('ctype', '', '--ctype', 'Type of cluster to start', compose(restrictValues(['ec2', 'nimbus']), notNone)),
    ('num', '', '--num', 'Number of nodes to create', compose(int, notNone)),
    ('update_dirs', '', '--update_dirs', 'Update scritps directories', defaultIfNone(False), True),
    ]

def updateCluster(cluster, mastL):
    """
    This keeps on setting the cluster master to the new value and
    dumping it to the database
    """
    master = mastL[0]
    debugPrint(lambda : 'Updating cluster: %s %s' % (master.publicDNS, master.state))
    cluster.setMaster(master)
    dump(cluster)
    


def addExecInstances(options, cl, tsk):
    ##
    # If there are other instances to be added then start them
    # and forward any messages onto the current task
    # if adding them fails, then throw an TryError
    # with 

    taskName = addInstances('localhost',
                            options('general.name'),
                            options('general.num'),
                            options('general.update_dirs'))
    endState, tsk = blockOnTaskAndForward('localhost',
                                          options('general.name'),
                                          taskName,
                                          tsk)
    if endState == task.TASK_FAILED:
        raise TryError('Failed to add instances to cluster', cl)

    return tsk


    
def main(options, _args):
    options = configFromMap(
        {'cluster': {'master_groups': [f.strip() for f in options('cluster.master_groups').split(',')],
                     'exec_groups': [f.strip() for f in options('cluster.exec_groups').split(',')],
                     }
         }, options)
    ctype = ec2control

    tsk = task.updateTask(task.loadTask(options('general.task_name')
                                        ).setState(task.TASK_RUNNING
                                                   ).addMessage(task.MSG_SILENT, 'Starting master'))
    
    cl = Cluster(options('general.name'), ctype, options)
    try:
        startMaster(cl, lambda m : updateCluster(cl, m), devMode=False, releaseCut=False)

        dump(cl)
        
        tsk = task.updateTask(tsk.progress())
        
        if options('general.num'):
            tsk = addExecInstances(options, cl, tsk)

        tsk = tsk.progress().setState(task.TASK_COMPLETED)
    except TryError, err:
        tsk = tsk.setState(task.TASK_COMPLETED).addMessage(task.MSG_ERROR, 'An error occured attempting to start the cluster:\n' + err.msg +
                                                           '\nThe cluster has been started as much as possible, it may not function properly though')
        dump(err.result)
    except Exception, err:
        tsk = task.updateTask(tsk.setState(task.TASK_FAILED
                                           ).addMessage(task.MSG_ERROR,
                                                        'An error occured attempting to start the cluster:\n' + str(err) + '\nExiting...'))
        raise


    tsk = task.updateTask(tsk)
        
if __name__ == '__main__':
    runCatchError(lambda : main(*buildConfigN(OPTIONS)),
                  mongoFail(dict(action='startCluster')))

#!/usr/bin/env python
##
# This script provides some insight into tasks
import sys

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.functional import identity
from igs.utils.logging import debugPrint
from igs.utils import logging

from vappio.webservice.task import loadAllTasks, loadTask

from vappio.tasks import task

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', notNone),
    ('read', '', '--read', 'Mark any messages as read', identity, True),
    ('show_msgs', '', '--show', 'Print out any messages present', identity, True),
    ('show_unread_msgs', '', '--show-unread', 'Print out only unread messages', identity, True),
    ('show_error_msgs', '', '--show-error', 'Print out only error messages', identity, True),
    ('show_debug_msgs', '', '--show-debug', 'Print out any debug messages', identity, True),
    ('debug', '', '--debug', 'Print debugging messages', identity, True),
    ('no_completed', '', '--nc', 'Filtered out completed tasks', identity, True),
    ('exit_code', '', '--exit-code', 'Exit with a non zero value if any tasks are not in a completed state', identity, True),
    ]

def main(options, tasks):
    if options('general.debug'):
        logging.DEBUG = True

    if options('general.read'):
        debugPrint(lambda : 'Will mark any messages unread as read')
        
    if not tasks:
        debugPrint(lambda : 'No task names provided, loading all from database')
        tasks = loadAllTasks(options('general.host'), options('general.name'), read=options('general.read'))
    else:
        debugPrint(lambda : 'Task names provided, loading from database')
        tasks = [loadTask(options('general.host'), options('general.name'), t, read=options('general.read'))
                 for t in tasks]

    if options('general.no_completed'):
        debugPrint(lambda : 'Removing any completed tasks')
        tasks = filter(lambda t : t.state != task.TASK_COMPLETED, tasks)


    maxTaskNameLen = max([len(t.name) for t in tasks])
    printSpacing = False
    for t in tasks:
        if not printSpacing:
            printSpacing = True
        else:
            print
            print

        print 'Task: %s%s State: %s%s Num: %d/%d (%3d%%)' % (t.name, ' ' * (maxTaskNameLen - len(t.name)),
                                                             t.state, ' ' * (13 - len(t.state)),
                                                             t.completedTasks,
                                                             t.numTasks,
                                                             int(float(t.completedTasks)/t.numTasks * 100.0))
        if options('general.show_msgs') or options('general.show_unread_msgs') or options('general.show_debug_msgs'):
            for m in t.messages:
                if m['mtype'] == task.MSG_NOTIFICATION and (options('general.show_msgs') or options('general.show_unread_msgs')):
                    print 'Notification: ' + m['data']
                elif m['mtype'] == task.MSG_ERROR and (options('general.show_msgs') or options('general.show_error_msgs')):
                    print 'Error: ' + m['data']
                elif m['mtype'] == task.MSG_SILENT and (options('general.show_msgs') or options('general.show_debug_msgs')):
                    print 'Debug: ' + m['data']

    if options('general.exit_code'):
        debugPrint(lambda : 'Exiting with non-zero state if any tasks are not in a completed state')
        notCompleted = [t for t in tasks if t.state != task.TASK_COMPLETED]
        if notCompleted:
            return 1
        else:
            return 0

    return 0

if __name__ == '__main__':
    sys.exit(main(*buildConfigN(OPTIONS)))


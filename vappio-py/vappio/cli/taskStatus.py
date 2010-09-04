#!/usr/bin/env python
##
# This script provides some insight into tasks
import sys
import time

from igs.utils.cli import buildConfigN, defaultIfNone
from igs.utils.functional import identity
from igs.utils.logging import debugPrint
from igs.utils import logging
from igs.utils import commands

from vappio.webservice.task import loadAllTasks, loadTask

from vappio.tasks import task

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster, defaults to local', defaultIfNone('local')),
    ('show_msgs', '', '--show', 'Print out any messages present', identity, True),
    ('show_error_msgs', '', '--show-error', 'Print out only error messages', identity, True),
    ('show_debug_msgs', '', '--show-debug', 'Print out any debug messages', identity, True),
    ('show_all_msgs', '', '--show-all', 'Print out all messages', identity, True),    
    ('debug', '', '--debug', 'Print debugging messages', identity, True),
    ('no_completed', '', '--nc', 'Filtered out completed tasks', identity, True),
    ('exit_code', '', '--exit-code', 'Exit with a non zero value if any tasks are not in a completed state', identity, True),
    ('block', '-b', '--block', 'Block on the tasks until they have completed or errored', identity, True),
    ]


def timestampToStr(ts):
    return time.strftime('%Y/%m/%d %H:%M:%S UTC', time.gmtime(ts))

def showAnyMsg(options):
    return (options('general.show_msgs') or
            options('general.show_error_msgs') or
            options('general.show_debug_msgs') or
            options('general.show_all_msgs'))


def printTask(options, t, maxTaskNameLen):
        print 'Task: %s%s Type: %s%s State: %s%s Num: %d/%d (%3d%%) LastUpdated: %s' % (t.name, ' ' * (maxTaskNameLen - len(t.name)),
                                                                                        t.tType, ' ' * (13 - len(t.tType)),
                                                                                        t.state, ' ' * (13 - len(t.state)),
                                                                                        t.completedTasks,
                                                                                        t.numTasks,
                                                                                        t.numTasks and int(float(t.completedTasks)/t.numTasks * 100.0) or 0,
                                                                                        timestampToStr(t.timestamp))
        if showAnyMsg(options):
            for m in t.messages:
                if m['mtype'] == task.MSG_NOTIFICATION and (options('general.show_msgs') or options('general.show_all_msgs')):
                    print 'Notification - %s: %s' % (timestampToStr(m['timestamp']), m['text'])
                elif m['mtype'] == task.MSG_ERROR and (options('general.show_error_msgs') or options('general.show_all_msgs')):
                    print 'Error - %s: %s' % (timestampToStr(m['timestamp']), m['text'])
                    if 'stacktrace' in m:
                        indented = '\n\t'.join(m['stacktrace'].split('\n'))
                        print 'Stacktrace:\n\t' + indented
                elif m['mtype'] == task.MSG_SILENT and (options('general.show_debug_msgs') or options('general.show_all_msgs')):
                    print 'Debug - %s: %s' % (timestampToStr(m['timestamp']), m['text'])
                elif options('general.show_all_msgs'):
                    print '%s - %s: %s' % (m['mtype'].title(), timestampToStr(m['timestamp']), repr(m))
    


def blockOnTasks(options, tasks):
    maxTaskNameLen = tasks and max([len(t.name) for t in tasks]) or 0
    ##
    # Loop until all of the tasks are in state FAILED or COMPLETED
    while [t for t in tasks if t.state not in [task.TASK_FAILED, task.TASK_COMPLETED]]:
        if showAnyMsg(options):
            commands.runSystem('clear')
            for t in tasks:
                printTask(options, t, maxTaskNameLen)
        time.sleep(30)
        tasks = [loadTask(options('general.host'), options('general.name'), t.name)
                 for t in tasks]

    ##
    # If we are showing any messages then clear the screen because after this
    # the tasks will be printed out again
    if showAnyMsg(options):
        commands.runSystem('clear')
        
    return tasks



def main(options, tasks):
    if options('general.debug'):
        logging.DEBUG = True

    if not tasks:
        debugPrint(lambda : 'No task names provided, loading all from database')
        tasks = loadAllTasks(options('general.host'), options('general.name'))
    else:
        debugPrint(lambda : 'Task names provided, loading from database')
        tasks = [loadTask(options('general.host'), options('general.name'), t)
                 for t in tasks]

    if options('general.block'):
        debugPrint(lambda : 'Blocking until tasks finish or fail')
        tasks = blockOnTasks(options, tasks)
        
    if options('general.no_completed'):
        debugPrint(lambda : 'Removing any completed tasks')
        tasks = filter(lambda t : t.state != task.TASK_COMPLETED, tasks)


    ##
    # If there are tasks, find the largest, otherwise just return 0
    maxTaskNameLen = tasks and max([len(t.name) for t in tasks]) or 0
    printSpacing = False
    for t in tasks:
        if not printSpacing:
            printSpacing = True
        else:
            print
            print

        printTask(options, t, maxTaskNameLen)

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


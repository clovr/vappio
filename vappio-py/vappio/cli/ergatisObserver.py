#!/usr/bin/env python
##
# This script observes a running pipeline and feeds updates back to the associated task

import sys

from igs.utils.cli import buildConfigN, notNone, restrictValues, defaultIfNone
from igs.utils.functional import identity

from vappio.webservice import task #import loadTask


OPTIONS = [
    ('event', '', '--event', 'Event', identity),
    ('name', '', '--name', 'Name', identity),
    ('retval', '', '--retval', 'Retval', identity),
    ('time', '', '--time', 'Time', identity),
    ('file', '', '--file', 'File', identity),
    ('id', '', '--ID', 'ID', identity),
    ('props', '', '--props', 'Props', identity),
    ('host', '', '--host', 'Host', identity),
    ('message', '', '--message', 'Message', identity)
    ]


def main(options, _args):
    ##
    # Let's log what's going on
    fout = open('/tmp/ergatisObserver.log', 'a')
    if options('general.event') == 'finish' and ' workflow' in options('general.message'):
        tsk = task.loadTask('localhost', 'local', options('general.props'))
        tsk = tsk.progress().addMessage(task.MSG_DEBUG, 'Completed ' + options('general.name'))
        task.updateTask(tsk)
        
        fout.write('%s finished  %s %s\n' % (options('general.name'), options('general.file'), options('general.retval')))
    elif int(options('general.retval')):
        tsk = task.loadTask('localhost', 'local', options('general.props'))
        tsk = tsk.setState(task.TASK_FAILED).addMessage(task.MSG_ERROR, 'Task failed on step ' + options('general.name'))
        task.updateTask(tsk)

        
        fout.write('%s %s %s %s\n' % (options('general.event'),
                                      options('general.name'),
                                      options('general.retval'),
                                      options('general.message')))
        

    
        

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

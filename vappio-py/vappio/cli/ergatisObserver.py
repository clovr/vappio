#!/usr/bin/env python
##
# This script observes a running pipeline and feeds updates back to the associated task
from xml.dom import minidom

from igs.utils.cli import buildConfigN, notNone, restrictValues, defaultIfNone
from igs.utils.functional import identity

from igs.xml.xmlquery import execQuery, name

from vappio.tasks import task



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


def pipelineProgress(workflowXML):
    doc = minidom.parse(workflowXML)
    query = [name('commandSetRoot'),
             [name('commandSet'),
              [name('status')]]]
    
    res = execQuery(query, doc)

    total = sum([int(r.childNodes[0].data) for r in res if r.localName == 'total'])
    complete = sum([int(r.childNodes[0].data) for r in res if r.localName == 'complete'])

    return (complete, total)
    

def main(options, _args):
    ##
    # Let's log what's going on
    fout = open('/tmp/ergatisObserver.log', 'a')
    if options('general.event') == 'finish' and options('general.retval') and not int(options('general.retval')):
        completed, total = pipelineProgress(options('general.file'))

        if completed != total:
            completed += 1
        
        tsk = task.loadTask(options('general.props'))
        tsk = tsk.update(completedTasks=completed, numTasks=total).addMessage(task.MSG_SILENT, 'Completed ' + options('general.name'))
        if  completed == total:
            tsk = tsk.setState(task.TASK_COMPLETED)
        task.updateTask(tsk)
        
        fout.write('%s finished  %s %s\n' % (options('general.name'), options('general.file'), options('general.retval')))
    elif options('general.retval') and int(options('general.retval')):
        tsk = task.loadTask(options('general.props'))
        if tsk.state != task.TASK_FAILED:
            tsk = tsk.setState(task.TASK_FAILED).addMessage(task.MSG_ERROR, 'Task failed on step ' + options('general.name'))
            task.updateTask(tsk)

        
        fout.write('%s %s %s %s\n' % (options('general.event'),
                                      options('general.name'),
                                      options('general.retval'),
                                      options('general.message')))
        

    
        

if __name__ == '__main__':
    try:
        main(*buildConfigN(OPTIONS))
    except Exception, err:
        open('/tmp/ergatisObserver.log', 'a').write(str(err) + '\n')

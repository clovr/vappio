from igs.utils.logging import logPrint, errorPrint, debugPrint
from igs.utils import logging

from vappio.webservice.task import loadTask

from vappio.tasks.task import getUnreadMessages, MSG_ERROR, MSG_NOTIFICATION, MSG_SILENT, TASK_FAILED, TASK_COMPLETED

def blockOnTask(host, name, taskName, notifyF=logPrint, errorF=errorPrint):
    state = None
    while state not in [TASK_FAILED, TASK_COMPLETED]:
        tsk = loadTask(host, name, taskName, read=True)
        state = tsk.state
        for m in getUnreadMessages(tsk):
            if m['mtype'] == MSG_ERROR:
                errorF(m['data'])
            elif m['mtype'] == MSG_NOTIFICATION:
                notifyF(m['data'])
            elif logging.DEBUG and m['mtype'] = MSG_SILENT:
                debugPrint(m['data'])
        ##
        # Make this configurable
        time.sleep(30)

    return state

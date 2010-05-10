
from igs.cgi.request import performQuery

from vappio.tasks.task import taskFromDict

TASK_URL = '/vappio/task_ws.py'

def loadTask(host, name, taskName, read=True):
    """
    Loads a task.  'read' means to mark any messages in the
    returned task as read or not
    """
    return taskFromDict(performQuery(host, TASK_URL, dict(name=name,
                                                          task_name=taskName,
                                                          read=read))[0])

def loadAllTasks(host, name, read=True):
    return [taskFromDict(t) for t in performQuery(host, TASK_URL, dict(name=name, read=read))]


    



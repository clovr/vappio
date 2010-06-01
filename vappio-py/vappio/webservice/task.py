
from igs.cgi.request import performQuery

from vappio.tasks.task import taskFromDict

TASK_URL = '/vappio/task_ws.py'

def loadTask(host, name, taskName):
    return taskFromDict(performQuery(host, TASK_URL, dict(name=name,
                                                          task_name=taskName))[0])

def loadAllTasks(host, name):
    return [taskFromDict(t) for t in performQuery(host, TASK_URL, dict(name=name))]


    



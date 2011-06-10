from igs_tx.utils import http

TASK_URL = '/vappio/task_ws.py'

def loadTask(host, clusterName, userName, taskName):
    return http.performQuery(host,
                             TASK_URL,
                             dict(cluster=clusterName,
                                  user_name=userName,
                                  task_name=taskName)).addCallback(lambda r : r[0])


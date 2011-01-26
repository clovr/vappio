##
# For persisting and loading tasks to the database
# This uses MongoDB has backend
import time

import pymongo

from igs.utils.functional import updateDict

class TaskDoesNotExistError(Exception):
    """A task does not exist in the db"""
    pass

def load(taskName, tries=3):
    task = pymongo.Connection().clovr.tasks.find_one(dict(name=taskName))
    if task is None and tries < 0:
        raise TaskDoesNotExistError(taskName)
    elif task is None:
        time.sleep(1)
        return load(taskName, tries - 1)
    else:
        return task

def dump(task):
    return pymongo.Connection().clovr.tasks.save(updateDict(dict(_id=task['name']), task))

def loadAll():
    return pymongo.Connection().clovr.tasks.find()

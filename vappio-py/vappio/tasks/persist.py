##
# For persisting and loading tasks to the database
# This uses MongoDB has backend

import pymongo

from igs.utils.functional import updateDict

class TaskDoesNotExistError(Exception):
    """A task does not exist in the db"""
    pass

def load(taskName):
    task = pymongo.Connection().clovr.tasks.find_one(dict(name=taskName))
    if task is None:
        raise TaskDoesNotExistError(taskName)
    return task

def dump(task):
    return pymongo.Connection().clovr.tasks.save(updateDict(dict(_id=task.name), task))


##
# For persisting and loading credentials to the database
# This uses MongoDB has backend

import pymongo

from igs.utils.functional import updateDict

class CredentialDoesNotExistError(Exception):
    """A task does not exist in the db"""
    pass

def load(credentialName):
    credential = pymongo.Connection().clovr.credentials.find_one(dict(name=credentialName))
    if credential is None:
        raise CredentialDoesNotExistError(taskName)
    return credential

def dump(credential):
    return pymongo.Connection().clovr.credentials.save(updateDict(dict(_id=credential['name']), credential))

def loadAll():
    return pymongo.Connection().clovr.credentials.find()

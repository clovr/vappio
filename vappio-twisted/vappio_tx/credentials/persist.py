import pymongo

from twisted.internet import threads
from twised.python import reflect

from igs.utils import functional as func


class CredentialDoesNotExistError(Exception):
    """A task does not exist in the db"""
    pass

class Credential(Record):
    """
    Represents a credentail that can actually be used (as opposed to copied outside of the machine)
    """
    pass


def createCredential(name, desc, ctype, cert, pkey, active, metadata):
    """
    name - a string naming the cred
    desc - a free form string describing the cred
    ctype - module/class that should be used to control a cluster in this credential
    cert - contents of certificate data
    pkey - contents of private key data
    active - if the account this credential is attached to is active or not
    metadata - a dictionary of miscellaneous values for the credential.  this dictionary MUST be
               convertable to json
    
    *** This is subject to change as this is a first pass
    """
    return Credential(name=name,
                      desc=desc,
                      ctype=reflect.fullyQualifiedName('vappio_tx.credentials.ctypes.' + ctype),
                      cert=cert,
                      pkey=pkey,
                      active=active,
                      metadata=metadata)


def credentialToDict(cred):
    """
    The main difference here is the ctype is turned into a string representation
    of the class/module name
    """
    return dict(name=cred.name,
                desc=cred.desc,
                ctype=reflect.fullyQualifiedName(cred.ctype),
                cert=cred.cert,
                pkey=cred.pkey,
                active=cred.active,
                metadata=cred.metadata)

def credentialFromDict(d):
    """
    Main difference is d['cert'] is a string for the module/class to use for this credential
    and this loads that module/class
    """
    return createCredential(d['name'],
                            d['desc'],
                            reflect.namedAny(d['ctype']),
                            d['cert'],
                            d['pkey'],
                            d['active'],
                            d['metadata'])


def loadCredential(credentialName):
    d = threads.deferToThread(lambda : pymongo.Connection().clovr.credentials.find_one(dict(name=credentialName)))

    def _credExists(credential):
        if credential is None:
            raise CredentialDoesNotExistError(credentialName)

        return credential

    d.addCallback(_credExists)
    d.addCallback(credentialFromDict)
    return d

def saveCredential(credential):
    d = threads.deferToThread(lambda : pymongo.Connection().clovr.credentials.save(func.updateDict(dict(_id=credential['name']),
                                                                                                   credentialToDict(credential))))
    return d

def loadAllCredentials():
    d = threads.deferToThread(lambda : pymongo.Connection().clovr.credentials.find())
    d.addCallback(lambda cs : [credentialFromDict(c) for c in cs])
    return d

def deleteCredential(credentialName):
    d = threads.deferToThread(lambda : pymongo.Connection().clovr.credentials.remove(dict(name=credentialName)))
    return d


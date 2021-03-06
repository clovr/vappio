import pymongo

from twisted.internet import threads
from twisted.internet import defer
from twisted.python import reflect

from igs.utils import functional as func
from igs.utils import config
from igs.utils import dependency

class Error(Exception):
    pass

class CredentialDoesNotExistError(Error):
    """A task does not exist in the db"""
    pass

class Credential(func.Record):
    """
    Represents a credentail that can actually be used (as opposed to copied outside of the machine)
    """

    def getCType(self):
        return reflect.fullyQualifiedName(self.ctype).split('.')[-1]


def createCredential(name, desc, ctype, cert, pkey, active, metadata, conf):
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

    #
    # Some transition code
    if ctype.startswith('vappio.'):
        ctype = ctype.split('.')[1]

    return Credential(name=name,
                      desc=desc,
                      ctype=reflect.namedAny('vappio_tx.credentials.ctypes.' + ctype),
                      cert=cert,
                      pkey=pkey,
                      active=active,
                      metadata=metadata,
                      conf=conf)


def credentialToDict(cred):
    """
    The main difference here is the ctype is turned into a string representation
    of the class/module name
    """
    return dict(name=cred.name,
                desc=cred.desc,
                ctype=cred.getCType(),
                cert=cred.cert,
                pkey=cred.pkey,
                active=cred.active,
                metadata=cred.metadata,
                conf=config.configToDict(cred.conf))

def credentialFromDict(d):
    """
    Main difference is d['cert'] is a string for the module/class to use for this credential
    and this loads that module/class
    """
    return createCredential(d['name'],
                            d['desc'],
                            d['ctype'],
                            d['cert'],
                            d['pkey'],
                            d['active'],
                            d['metadata'],
                            config.configFromMap(d['conf']))

class CredentialPersistManager(dependency.Dependable):
    def __init__(self):
        dependency.Dependable.__init__(self)

    @defer.inlineCallbacks
    def loadCredential(self, credentialName):
        credential = yield threads.deferToThread(lambda : pymongo.Connection().clovr.credentials.find_one(dict(name=credentialName)))

        if credential is None:
            raise CredentialDoesNotExistError(credentialName)
        
        self.changed('load', credential)
        defer.returnValue(credentialFromDict(credential))

    @defer.inlineCallbacks
    def saveCredential(self, credential):
        savedCred = yield threads.deferToThread(lambda : pymongo.Connection().clovr.credentials.save(func.updateDict(dict(_id=credential.name),
                                                                                                                     credentialToDict(credential)),
                                                                                                     safe=True))
        
        self.changed('save', savedCred)
        defer.returnValue(savedCred)

    @defer.inlineCallbacks
    def loadAllCredentials(self):
        credentialsDicts = yield threads.deferToThread(lambda : pymongo.Connection().clovr.credentials.find())
        credentials = [credentialFromDict(c) for c in credentialsDicts]
        self.changed('load_all', credentials)
        defer.returnValue(credentials)

    @defer.inlineCallbacks
    def deleteCredential(self, credentialName):
        yield threads.deferToThread(lambda : pymongo.Connection().clovr.credentials.remove(dict(name=credentialName)))
        self.changed('delete', credentialName)

from twisted.python import reflect

from igs.utils.functional import Record

from vappio.credentials import persist

class Credential(Record):
    """
    Don't need anything special for this yet but assuming
    I will
    """
    pass

class PublicCredential(Record):
    """
    This represents a credential that is okay to be public.
    It does not contain any secret credential information
    """
    pass



def publicCredentialFromDict(d):
    return PublicCredential(name=d['name'],
                            desc=d['desc'],
                            ctype=d['ctype'])

def publicCredentialToDict(pcred):
    return dict(name=pcred.name,
                desc=pcred.desc,
                ctype=pcred.ctype)


def credentialToDict(cred):
    """
    The main difference here is the ctype is turned into a string representation
    of the class/module name
    """
    return dict(name=name,
                desc=desc,
                ctype=ctype,
                cert=reflect.fullyQualifiedName(cert),
                pkey=pkey)

def credentialFromDict(d):
    """
    Main difference is d['cert'] is a string for the module/class to use for this credential
    and this loads that module/class
    """
    return createCredential(d['name'],
                            d['desc'],
                            d['ctype'],
                            reflect.namedAny(d['cert']),
                            d['pkey'])

def createCredential(name, desc, ctype, cert, pkey):
    """
    name - a string naming the cred
    desc - a free form string describing the cred
    ctype - module/class that should be used to control a cluster in this credential
    cert - contents of certificate data
    pkey - contents of private key data

    *** This is subject to change as this is a first pass
    """
    return Credential(name=name, desc=desc, ctype=ctype, cert=cert, pkey=pkey)

def loadCredential(name):
    return credentialFromDict(persist.load(name))

def loadAllCredentails():
    return [credentialFromDict(c) for c in persist.loadAll()]

def saveCredential(cred):
    return credentialToDict(persist.dump(cred))


def ctypeNameToInstance(name):
    """
    This takes a name like ec2 or nimbus and returns an instantiation of
    the control module (the ctype).
    """
    return reflect.namedAny('vappio.' + name + '.control')

def credentialToPublicCredential(cred):
    return PublicCredential(name=cred.name,
                            desc=cred.desc,
                            ctype=cred.ctype.name)

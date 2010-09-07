
from igs.cgi.request import performQuery

from vappio.credentials import manager

CREDENTIAL_URL = '/vappio/credential_ws.py'


def saveCredential(host, name, cred):
    return performQuery(host, CREDENTIAL_URL, dict(name=name,
                                                   cred=manager.credentialToDict(cred)))
                                                   


def loadCredentials(host, name):
    return [manager.publicCredentialFromDict(c) for c in performQuery(host, CREDENTIAL_URL, dict(name=name))]

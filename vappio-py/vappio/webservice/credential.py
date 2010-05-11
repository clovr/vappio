
from igs.cgi.request import performQuery

from vappio.credentials.manager import credentialToDict

CREDENTIAL_URL = '/vappio/credential_ws.py'


def saveCredential(host, name, cred):
    return performQuery(host, CREDENTIAL_URL, dict(name=name,
                                                   cred=credentialToDict(cred)))
                                                   


def listCredentials(host, name):
    return performQuery(host, CREDENTIAL_URL, dict(name=name))


from igs.cgi.request import performQuery

CREDENTIAL_URL = '/vappio/credential_ws.py'


def saveCredential(host, name, cred):
    return performQuery(host, CREDENTIAL_URL, dict(name=name,
                                                   cred=manager.credentialToDict(cred)))
def loadCredentials(host, cluster, credNames):
    request = dict(cluster=cluster)
    if credNames:
        request['credential_names'] = credNames
    return performQuery(host, CREDENTIAL_URL, request)

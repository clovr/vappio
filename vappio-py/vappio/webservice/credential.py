
from igs.cgi.request import performQuery

CREDENTIAL_URL = '/vappio/credential_ws.py'


def saveCredential(host, name, cred_name, desc, ctype, cert, pkey, metadata):
    return performQuery(host, CREDENTIAL_URL, dict(cluster=name,
                                                   credential_name=cred_name,
                                                   description=desc,
                                                   ctype=ctype,
                                                   cert=cert,
                                                   pkey=pkey,
                                                   metadata=metadata))
def loadCredentials(host, cluster, credNames):
    request = dict(cluster=cluster)
    if credNames:
        request['credential_names'] = credNames
    return performQuery(host, CREDENTIAL_URL, request)

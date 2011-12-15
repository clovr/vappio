
from igs.cgi.request import performQuery

CREDENTIAL_URL = '/vappio/credential_ws.py'
DELETE_URL = '/vappio/credential_delete'

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

def deleteCredential(host, cluster, credName, dryRun):
    return performQuery(host, DELETE_URL, dict(cluster=cluster,
                                               credential_name=credName,
                                               dry_run=dryRun))

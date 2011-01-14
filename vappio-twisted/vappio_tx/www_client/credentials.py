from igs_tx.utils import http

SAVECREDENTIAL_URL = '/vappio/credential_ws.py'

def saveCredential(host, clusterName, credName, description, ctype, cert, pkey, metadata):
    return http.performQuery(host,
                             SAVECREDENTIAL_URL,
                             dict(cluster=clusterName,
                                  credential_name=credName,
                                  description=description,
                                  ctype=ctype,
                                  cert=cert,
                                  pkey=pkey,
                                  metadata=metadata))

def listCredentials(host, clusterName):
    return http.performQuery(host,
                             SAVECREDENTIAL_URL,
                             dict(cluster=clusterName))

def describeCredentials(host, clusterName, credentials):
    return http.performQuery(host,
                             SAVECREDENTIAL_URL,
                             dict(cluster=clusterName,
                                  credential_names=credentials))

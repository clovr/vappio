from twisted.internet import defer

@defer.inlineCallbacks
def loadCredentialForRequest(request):
    credential = yield request.state.credentialsCache.loadAndCacheCredential(request.body['credential_name'])
    defer.returnValue(request.update(credential=credential))

def replaceUserDataVariables(cred, userData):
    userData = userData.replace('<TMPL_VAR NAME=CERT_FILE>', open(cred.credInstance.cert).read())
    userData = userData.replace('<TMPL_VAR NAME=PK_FILE>', open(cred.credInstance.pkey).read())
    userData = userData.replace('<TMPL_VAR NAME=CTYPE>', cred.credential.getCType())
    userData = userData.replace('<TMPL_VAR NAME=METADATA>', ','.join([str(k) + '=' + str(v) for k, v in cred.credential.metadata.iteritems()]))

    return userData

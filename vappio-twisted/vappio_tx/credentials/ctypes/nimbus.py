import os
import urlparse

from twisted.internet import reactor
from twisted.internet import defer

from twisted.python import log

from igs_tx.utils import commands
from igs_tx.utils import defer_utils

from igs.utils import functional as func
from igs.utils import config

from vappio_tx.credentials.ctypes import ec2


##
# This module wants to go by
NAME = 'Nimbus'
DESC = """Control module for Nimbus-based users"""

RETRY_ATTEMPTS = 10

def instantiateCredential(conf, cred):
    if not conf('config_loaded', default=False):
        conf = config.configFromConfig(conf,
                                       base=config.configFromStream(open(conf('conf_file')),
                                                                    base=conf))

    certFile = os.path.join(conf('general.secure_tmp'), cred.name + '_cert.pem')
    keyFile = os.path.join(conf('general.secure_tmp'), cred.name + '_key.pem')

    mainDeferred = defer.succeed(None)
    
    if not os.path.exists(certFile) and not os.path.exists(keyFile):
        tmpCertFile = os.path.join(conf('general.secure_tmp'), cred.name + '_cert-tmp.pem')
        tmpKeyFile = os.path.join(conf('general.secure_tmp'), cred.name + '_key-tmp.pem')
        if 'ec2_url' not in cred.metadata:
            return defer.fail(Exception('You must have an ec2_url'))
        parsedUrl = urlparse.urlparse(cred.metadata['ec2_url'])
        if ':' not in parsedUrl.netloc:
            return defer.fail(Exception('Your URL must contain a port'))
        host, port = parsedUrl.netloc.split(':')
        fout = open(tmpCertFile, 'w')
        fout.write(cred.cert)
        fout.close()
        fout = open(tmpKeyFile, 'w')
        fout.write(cred.pkey)
        fout.close()
        d = commands.runProcess(['nimbusCerts2EC2.py',
                                 '--in-cert=' + tmpCertFile,
                                 '--out-cert=' + certFile,
                                 '--in-key=' + tmpKeyFile,
                                 '--out-key=' + keyFile,
                                 '--java-cert-dir=/tmp',
                                 '--java-cert-host=' + host,
                                 '--java-cert-port=' + port],
                                stdoutf=None,
                                stderrf=None,
                                log=True)

        def _chmod(_exitCode):
            return commands.runProcess(['chmod', '+r', keyFile], stdoutf=None, stderrf=None)

        d.addCallback(_chmod)

        def _unlink(v):
            os.unlink(tmpCertFile)
            os.unlink(tmpKeyFile)
            return v

        d.addCallback(_unlink)
        d.addErrback(_unlink)

        mainDeferred.addCallback(lambda _ : d)
        
    ec2Home = '/opt/ec2-api-tools-1.3-42584'
    newCred = func.Record(name=cred.name, conf=conf, cert=certFile, pkey=keyFile, ec2Path=os.path.join(ec2Home, 'bin'),
                          env=dict(EC2_JVM_ARGS='-Djavax.net.ssl.trustStore=/tmp/jssecacerts',
                                   EC2_HOME=ec2Home,
                                   EC2_URL=cred.metadata['ec2_url']))
    if os.path.exists(conf('cluster.cluster_private_key') + '.pub'):
        pubKey = open(conf('cluster.cluster_private_key') + '.pub').read().rstrip()
        def _addKeypair():
            keyPairDefer = ec2.addKeypair(newCred, '"' + conf('cluster.key') + '||' + pubKey + '"')
            def _printError(f):
                log.msg('Adding keypaired failed, retrying')
                log.err(f)
                return f
            keyPairDefer.addErrback(_printError)
            return keyPairDefer
        mainDeferred.addCallback(lambda _ : defer_utils.tryUntil(10, _addKeypair, onFailure=defer_utils.sleep(30)))
        
    mainDeferred.addCallback(lambda _ : newCred)
    return mainDeferred


def retryIfTTLError(fail):
    try:
        fail.raiseException()
    except commands.ProgramRunError, err:
        return defer.succeed('General security' in err.stderr)
    except Exception:
        return fail


def retry(n, f):
    def _(*args, **kwargs):
        return defer_utils.tryUntil(n,
                                    lambda : f(*args, **kwargs),
                                    onFailure=defer_utils.sleep(30),
                                    retry=retryIfTTLError)

    return _



# Set all of these to what ec2 does
Instance = ec2.Instance
instanceFromDict = ec2.instanceFromDict
instanceToDict = ec2.instanceToDict

addGroup = retry(RETRY_ATTEMPTS, ec2.addGroup)
addKeypair = retry(RETRY_ATTEMPTS, ec2.addKeypair)
authorizeGroup = retry(RETRY_ATTEMPTS, ec2.authorizeGroup)
listGroups = retry(RETRY_ATTEMPTS, ec2.listGroups)
listInstances = retry(RETRY_ATTEMPTS, ec2.listInstances)
listKeypairs = retry(RETRY_ATTEMPTS, ec2.listKeypairs)
runInstances = retry(RETRY_ATTEMPTS, ec2.runInstances)
runSpotInstances = retry(RETRY_ATTEMPTS, ec2.runSpotInstances)
updateInstances = retry(RETRY_ATTEMPTS, ec2.updateInstances)
terminateInstances = retry(RETRY_ATTEMPTS, ec2.terminateInstances)

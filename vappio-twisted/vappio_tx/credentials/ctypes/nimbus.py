import os
import urlparse

from twisted.internet import defer

from igs_tx.utils import commands

from igs.utils import functional as func
from igs.utils import config

from vappio.ec2 import control as ec2_control


##
# This module wants to go by
NAME = 'Nimbus'
DESC = """Control module for Nimbus-based users"""


def instantiateCredential(conf, cred):
    if not conf('config_loaded', default=False):
        conf = config.configFromMap({'config_loaded': True},
                                    base=config.configFromStream(open(conf('general.conf_file')), base=conf))
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

        d.addCallback(_unlink)
        d.addErrback(_unlink)

        mainDeferred.addCallback(lambda _ : d)
        
    ec2Home = '/opt/ec2-api-tools-1.3-42584'
    newCred = func.Record(cert=certFile, pkey=keyFile, ec2Path=os.path.join(ec2Home, 'bin'),
                          env=dict(EC2_JVM_ARGS='-Djavax.net.ssl.trustStore=/tmp/jssecacerts',
                                   EC2_HOME=ec2Home,
                                   EC2_URL=cred.metadata['ec2_url']))
    if os.path.exists(conf('cluster.cluster_private_key') + '.pub'):
        pubKey = open(conf('cluster.cluster_private_key') + '.pub').read().rstrip()
        mainDeferred.addCallback(lambda _ : ec2_control.addKeypair(newCred, '"' + conf('cluster.key') + '||' + pubKey + '"'))
        
    mainDeferred.addCallback(lambda _ : (conf, newCred))
    return mainDeferred
        


# Set all of these to what ec2 does
Instance = ec2_control.Instance
addGroup = ec2_control.addGroup
addKeypair = ec2_control.addKeypair
authorizeGroup = ec2_control.authorizeGroup
instanceFromDict = ec2_control.instanceFromDict
instanceToDict = ec2_control.instanceToDict
listGroups = ec2_control.listGroups
listInstances = ec2_control.listInstances
listKeypairs = ec2_control.listKeypairs
runInstances = ec2_control.runInstances
runSpotInstances = ec2_control.runSpotInstances
terminateInstances = ec2_control.terminateInstances
updateInstances = ec2_control.updateInstances

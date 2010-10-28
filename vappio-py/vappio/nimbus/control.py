import os
import urlparse

from igs.utils import commands
from igs.utils import functional as func

from vappio.ec2 import control as ec2_control


##
# This module wants to go by
NAME = 'Nimbus'
DESC = """Control module for Nimbus-based users"""


def instantiateCredential(conf, cred):
    certFile = os.path.join(conf('general.secure_tmp'), cred.name + '_cert.pem')
    keyFile = os.path.join(conf('general.secure_tmp'), cred.name + '_key.pem')
    if not os.path.exists(certFile) and not os.path.exists(keyFile):
        tmpCertFile = os.path.join(conf('general.secure_tmp'), cred.name + '_cert-tmp.pem')
        tmpKeyFile = os.path.join(conf('general.secure_tmp'), cred.name + '_key-tmp.pem')
        if 'ec2_url' not in cred.metadata:
            raise Exception('You must have an ec2_url')
        parsedUrl = urlparse.urlparse(cred.metadata['ec2_url'])
        if ':' not in parsedUrl.netloc:
            raise Exception('Your URL must contain a port')
        host, port = parsedUrl.netloc.split(':')
        fout = open(tmpCertFile, 'w')
        fout.write(cred.cert)
        fout.close()
        fout = open(tmpKeyFile, 'w')
        fout.write(cred.pkey)
        fout.close()
        commands.runSystemEx(' '.join(['nimbusCerts2EC2.py',
                                       '--in-cert=' + tmpCertFile,
                                       '--out-cert=' + certFile,
                                       '--in-key=' + tmpKeyFile,
                                       '--out-key=' + keyFile,
                                       '--java-cert-dir=/tmp',
                                       '--java-cert-host=' + host,
                                       '--java-cert-port=' + port]) + ' > /dev/null 2>&1', log=True)
        commands.runSystemEx('chmod +r ' + keyFile)
    ec2Home = '/opt/ec2-api-tools-1.3-42584'
    newCred = func.Record(cert=certFile, pkey=keyFile, ec2Path=os.path.join(ec2Home, 'bin'),
                          env=dict(EC2_JVM_ARGS='-Djavax.net.ssl.trustStore=/tmp/jssecacerts',
                                   EC2_HOME=ec2Home,
                                   EC2_URL=cred.metadata['ec2_url']))
    if conf('cluster.cluster_private_key') + '.pub':
        pubKey = open(conf('cluster.cluster_private_key') + '.pub').read().rstrip()
        ec2_control.addKeypair(newCred, '"' + conf('cluster.key') + '||' + pubKey + '"')
    return newCred
        


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

from twisted.internet import defer
from twisted.internet import reactor

from igs.utils import config

from vappio_tx.credentials.ctypes import nimbus


##
# This module wants to go by
NAME = 'DIAG'
DESC = """Control module for DIAG users"""

DEFAULT_CONFIG_FILE = '/mnt/vappio-conf/clovr_diag.conf'
DIAG_EC2_URL = 'https://diagcloud.igs.umaryland.edu:8443/wsrf/services/ElasticNimbusService'

def instantiateCredential(conf, cred):
    if 'ec2_url' not in cred.metadata:
        cred.metadata['ec2_url'] = DIAG_EC2_URL
    if 'conf_file' not in conf or not conf('conf_file'):
        conf = config.configFromMap({'conf_file': DEFAULT_CONFIG_FILE}, base=conf)
    return nimbus.instantiateCredential(conf, cred)


def terminateInstances(cred, instances):
    """DIAG errors out so often here we want to consume them, instances still terminate"""
    d = defer.Deferred()
    def loop(tries):
        terminateDefer = nimbus.terminateInstances(cred, instances)
        terminateDefer.addCallback(lambda _ : d.callback(True))
        if tries > 0:
            terminateDefer.addErrback(lambda _ : reactor.callLater(30, loop, tries - 1))
        else:
            terminateDefer.addErrback(d.errback)
    loop(10)
    return d

# Set all of these to what nimbus does
Instance = nimbus.Instance
instanceFromDict = nimbus.instanceFromDict
instanceToDict = nimbus.instanceToDict
addGroup = nimbus.addGroup
addKeypair = nimbus.addKeypair
authorizeGroup = nimbus.authorizeGroup
listGroups = nimbus.listGroups
listInstances = nimbus.listInstances
listKeypairs = nimbus.listKeypairs
runInstances = nimbus.runInstances
runSpotInstances = nimbus.runSpotInstances
updateInstances = nimbus.updateInstances

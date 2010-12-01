import os
import urlparse

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
        

# Set all of these to what nimbus does
Instance = nimbus.Instance
addGroup = nimbus.addGroup
addKeypair = nimbus.addKeypair
authorizeGroup = nimbus.authorizeGroup
instanceFromDict = nimbus.instanceFromDict
instanceToDict = nimbus.instanceToDict
listGroups = nimbus.listGroups
listInstances = nimbus.listInstances
listKeypairs = nimbus.listKeypairs
runInstances = nimbus.runInstances
runSpotInstances = nimbus.runSpotInstances
terminateInstances = nimbus.terminateInstances
updateInstances = nimbus.updateInstances

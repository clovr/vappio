import os
import urlparse

from igs.utils import commands
from igs.utils import functional as func
from igs.utils import config

from vappio.nimbus import control as nimbus_control


##
# This module wants to go by
NAME = 'DIAG'
DESC = """Control module for DIAG users"""

DEFAULT_CONFIG_FILE = '/mnt/vappio-conf/clovr_diag.conf'
DIAG_EC2_URL = 'https://diagcloud.igs.umaryland.edu:8443/wsrf/services/ElasticNimbusService'

def instantiateCredential(conf, cred):
    if 'ec2_url' not in cred.metadata:
        cred.metadata['ec2_url'] = DIAG_EC2_URL
    if 'general.conf_file' not in conf or not conf('general.conf_file'):
        conf = config.configFromMap({'general.conf_file': DEFAULT_CONFIG_FILE}, base=conf)
    return nimbus_control.instantiateCredential(conf, cred)
        

# Set all of these to what nimbus does
Instance = nimbus_control.Instance
addGroup = nimbus_control.addGroup
addKeypair = nimbus_control.addKeypair
authorizeGroup = nimbus_control.authorizeGroup
instanceFromDict = nimbus_control.instanceFromDict
instanceToDict = nimbus_control.instanceToDict
listGroups = nimbus_control.listGroups
listInstances = nimbus_control.listInstances
listKeypairs = nimbus_control.listKeypairs
runInstances = nimbus_control.runInstances
runSpotInstances = nimbus_control.runSpotInstances
terminateInstances = nimbus_control.terminateInstances
updateInstances = nimbus_control.updateInstances

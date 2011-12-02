from twisted.internet import defer
from twisted.internet import reactor

from igs.utils import config

from vappio_tx.credentials.ctypes import nimbus
from vappio_tx.credentials.ctypes import ec2

##
# This module wants to go by
NAME = 'DIAG'
DESC = """Control module for DIAG users"""

DEFAULT_CONFIG_FILE = '/mnt/vappio-conf/clovr_diag.conf'
DIAG_EC2_URL = 'https://nimbus.diagcomputing.org:8443/wsrf/services/ElasticNimbusService'

INSTANCE_TYPE_MAPPING = {'default': 'm1.small',
                         'small': 'm1.small',
                         'medium': 'm1.large',
                         'large': 'm1.xlarge',
                         }


def instantiateCredential(conf, cred):
    if 'ec2_url' not in cred.metadata:
        cred.metadata['ec2_url'] = DIAG_EC2_URL
    if 'conf_file' not in conf or not conf('conf_file'):
        conf = config.configFromMap({'conf_file': DEFAULT_CONFIG_FILE}, base=conf)
    return nimbus.instantiateCredential(conf, cred)

    
def runInstances(cred,
                 amiId,
                 key,
                 instanceType,
                 groups,
                 availabilityZone=None,
                 number=None,
                 userData=None,
                 userDataFile=None,
                 log=False):
    return nimbus.runInstances(cred,
                               amiId,
                               key,
                               ec2.mapInstanceType(INSTANCE_TYPE_MAPPING, instanceType),
                               groups,
                               availabilityZone,
                               number,
                               userData,
                               userDataFile,
                               log)

def runSpotInstances(cred,
                     bidPrice,
                     amiId,
                     key,
                     instanceType,
                     groups,
                     availabilityZone=None,
                     number=None,
                     userData=None,
                     userDataFile=None,
                     log=False):
    return nimbus.runInstances(cred,
                               bidPrice,
                               amiId,
                               key,
                               ec2.mapInstanceType(INSTANCE_TYPE_MAPPING, instanceType),
                               groups,
                               availabilityZone,
                               number,
                               userData,
                               userDataFile,
                               log)    

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
updateInstances = nimbus.updateInstances
terminateInstances = nimbus.terminateInstances

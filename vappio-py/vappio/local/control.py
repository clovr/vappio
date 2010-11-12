from igs.utils import config

from vappio.ec2 import control as ec2control


##
# This module wants to go by
NAME = 'local'
DESC = """Control module for local, mostly NOOPs"""

DEFAULT_CONFIG_FILE = '/mnt/vappio-conf/clovr.conf'

##
# Look just like EC2's instance
Instance = ec2control.Instance
instanceToDict = ec2control.instanceToDict
instanceFromDict = ec2control.instanceFromDict



def instantiateCredential(conf, cred):
    if not conf('config_loaded', default=False):
        conf = config.configFromMap({'config_loaded': True},    
                                    base=config.configFromStream(open(conf('general.conf_file', default=DEFAULT_CONFIG_FILE)), base=conf))
    return (conf, None)

def runInstances(cred, *args, **kwargs):
    return []


def runSpotInstances(cred, *args, **kwargs):
    return []


def listInstances(cred, log=False):
    return []
                 

def terminateInstances(cred, instances, log=False):
    return None

def updateInstances(cred, instances, log=False):
    return instances

def listKeypairs(cred, log=False):
    return []

def addKeypair(cred, name, log=False):
    return None

def listGroups(cred, log=False):
    return []
        
def addGroup(cred, name, description, log=False):
    return None

def authorizeGroup(cred,
                   groupName,
                   protocol,
                   portRange,
                   sourceGroup=None,
                   sourceGroupUser=None,
                   sourceSubnet=None,
                   log=False):
    return None

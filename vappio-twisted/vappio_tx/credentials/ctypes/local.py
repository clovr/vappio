from twisted.internet import defer

from igs.utils import config
from igs.utils import functional as func

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
    if 'conf_file' not in conf or not conf('conf_file'):
        conf = config.configFromMap({'conf_file': DEFAULT_CONFIG_FILE}, base=conf)    

    newCred = func.Record(name=cred.name, conf=conf)
    return defer.succeed(newCred)

def runInstances(cred, *args, **kwargs):
    return defer.succeed([])


def runSpotInstances(cred, *args, **kwargs):
    return defer.succeed([])


def listInstances(cred, log=False):
    return defer.succeed([])
                 

def terminateInstances(cred, instances, log=False):
    return defer.succeed(None)

def updateInstances(cred, instances, log=False):
    return defer.succeed(instances)

def listKeypairs(cred, log=False):
    return defer.succeed([])

def addKeypair(cred, name, log=False):
    return defer.succeed(None)

def listGroups(cred, log=False):
    return defer.succeed([])
        
def addGroup(cred, name, description, log=False):
    return defer.succeed(None)

def authorizeGroup(cred,
                   groupName,
                   protocol,
                   portRange,
                   sourceGroup=None,
                   sourceGroupUser=None,
                   sourceSubnet=None,
                   log=False):
    return defer.succeed(None)

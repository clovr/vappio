from vappio.ec2 import control as ec2control


##
# This module wants to go by
NAME = 'local'
DESC = """Control module for local, mostly NOOPs"""

##
# Look just like EC2's instance
Instance = ec2control.Instance
instanceToDict = ec2control.instanceToDict
instanceFromDict = ec2control.instanceFromDict



def instantiateCredential(conf, cred):
    return None

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

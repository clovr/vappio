
from vappio.ec2 import control


##
# This module wants to go by
NAME = 'DIAG'
DESC = """Control module for DIAG"""


def instantiateCredential(conf, cred):
    cred = control.instantiateCredential(conf, cred)
    



# Set all of these to what ec2 does
Instance = control.Instance
addGroup = control.addGroup
addKeypair = control.addKeypair
authorizeGroup = control.authorizeGroup
instanceFromDict = control.instanceFromDict
instanceToDict = control.instanceToDict
listGroups = control.listGroups
listInstances = control.listInstances
listKeypairs = control.listKeypairs
runInstances = control.runInstances
runSpotInstances = control.runSpotInstances
terminateInstances = control.terminateInstances
updateInstances = control.updateInstances

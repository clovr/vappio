##
# This has functions wrapping ec2 functionality.  This is currently implemented
# by wrapping the ec2-api tools binaries but it could be replaced by something like Boto.
# The reason binaries are being wrapped here is because the nimbus clouds require a specific
# version of the tools and it would be easier to use a single code-base for controlling thigns
# with EC2 (the nimbus stuff can just call this).  For that reason, the ec2-bins are wrapped
# otherwise we could get into a situationw here Boto implements one version of the tools and
# it does not work on NIMBUS but on ec2 or vice versa.

from igs.utils import logging
from igs.utils.logging import logPrint, errorPrint, debugPrint
from igs.utils.commands import runSystemEx, runSingleProgram, runProgramRunnerEx, ProgramRunner

##
# This module wants to go by
NAME = 'EC2'
DESC = """Control module for EC2"""

class Instance:
    """Represents running image"""

    ##
    # The state variables
    RUNNING = 'running'
    TERMINATED = 'terminated'
    PENDING = 'pending'
    SHUTTINGDOWN = 'shutting-down'
    
    def __init__(self,
                 instanceId,
                 amiId,
                 pubDns,
                 privDns,
                 state,
                 key,
                 index,
                 instanceType,
                 launch,
                 availabilityZone,
                 monitor):

        self.instanceId = instanceId
        self.amiId = amiId
        self.publicDNS = pubDns
        self.privateDNS = privDns
        self.state = state
        self.key = key
        self.index = index
        self.instanceType = instanceType
        self.launch = launch
        self.availabilityZone = availabilityZone
        self.monitor = monitor

    def __str__(self):
        return 'Instance%r' % ((self.instanceId,
                                self.amiId,
                                self.publicDNS,
                                self.privateDNS,
                                self.state,
                                self.key,
                                self.index,
                                self.instanceType,
                                self.launch,
                                self.availabilityZone,
                                self.monitor),)


def instanceToDict(instance):
    return dict(instanceId=instance.instanceId,
                amiId=instance.amiId,
                publicDNS=instance.publicDNS,
                privateDNS=instance.privateDNS,
                state=instance.state,
                key=instance.key,
                index=instance.index,
                instanceType=instance.instanceType,
                launch=instance.launch,
                availabilityZone=instance.availabilityZone,
                monitor=instance.monitor)

def instanceFromDict(d):
    return Instance(d['instanceId'],
                    d['amiId'],
                    d['publicDNS'],
                    d['privateDNS'],
                    d['state'],
                    d['key'],
                    d['index'],
                    d['instanceType'],
                    d['launch'],
                    d['availabilityZone'],
                    d['monitor'])

    
def ctorProgramRunner(cmd, stdoutf=logging.OUTSTREAM.write, stderrf=logging.ERRSTREAM.write, log=False):
    return ProgramRunner(cmd, stdoutf, stderrf, log=log)


def parseInstanceLine(line):
    if line.startswith('INSTANCE'):
        try:
            sline = line.strip().split('\t')
            _, instanceId, amiId, pubDns, privDns, state, key, index, _unsure, t, launch, zone, monitor = sline[:13]

            return Instance(instanceId,
                            amiId,
                            pubDns,
                            privDns,
                            state,
                            key,
                            index,
                            t,
                            launch,
                            zone,
                            monitor)
        except ValueError:
            errorPrint('Failed to parse line: ' + line)
            return None
    else:
        return None



def runInstancesA(instances,
                  amiId,
                  key,
                  instanceType,
                  groups,
                  availabilityZone=None,
                  number=None,
                  userData=None,
                  userDataFile=None,
                  log=False):
    """
    This returns a ProgramRunner that can be used asychronously

    instances - a list that will be populated with the running instances - weak sauce, work on fixing this
    amiId - string representing the AMI id
    key - string for keypair to use
    instanceType - string for instance type
    groups - list of groups to be included in
    availabilityZone - string for availability zone
    userData - optional user data string to send
    userDataFile - optional user data file to send
    """
    def _instanceParse(line):
        instance = parseInstanceLine(line)
        if instance:
            instances.append(instance)
    
    ##
    # make base command
    cmd = ['ec2-run-instances',
           amiId,
           '-k ' + key,
           '-t ' + instanceType]

    if availabilityZone:
        cmd.append('-z %s' % availabilityZone)

    ##
    # add groups
    for g in groups:
        cmd.append('-g ' +  g)

    if number:
        cmd.append('-n %d ' % number)

    if userData:
        cmd.append('-d ' + userData)

    if userDataFile:
        cmd.append('-f ' + userDataFile)

    return ctorProgramRunner(' '.join(cmd), _instanceParse, log=log)

def runInstances(*args, **kwargs):
    """Blocking version of runInstancesA, this returns a list of instances"""
    instances = []
    runProgramRunnerEx(runInstancesA(instances, *args, **kwargs))
    return instances

def listInstancesA(instances, log=False):
    """List all currently running instances"""
    def _instanceParse(line):
        instance = parseInstanceLine(line)
        if instance:
            instances.append(instance)

    return ctorProgramRunner('ec2-describe-instances', _instanceParse, log=log)

def listInstances(log=False):
    """Blocking version, returns list of instances"""
    instances = []
    runProgramRunnerEx(listInstancesA(instances, log=log))
    return instances
                 
def terminateInstancesA(instances, log=False):
    """Asynchronous, terminate all instances that match the filter function"""
    return ctorProgramRunner('ec2-terminate-instances ' + ' '.join([i.instanceId for i in instances]), log=log)

def terminateInstances(instances, log=False):
    runProgramRunnerEx(terminateInstancesA(instances, log=log))
    
    
def updateInstancesA(retInst, instances, log=False):
    """
    Updates the list of states of the instances given.

    retInst - List that will be filled with values of the new instances
    instances - List of instances that should be updated
    """

    instanceSet = set([i.instanceId for i in instances])

    def _instanceParse(line):
        instance = parseInstanceLine(line)
        if instance and instance.instanceId in instanceSet:
            retInst.append(instance)


    return ctorProgramRunner('ec2-describe-instances', _instanceParse, log=log)


def updateInstances(instances, log=False):
    retInst = []
    runProgramRunnerEx(updateInstancesA(retInst, instances, log=log))
    return retInst

def listKeypairsA(keypairs, log=False):
    """
    Returns a list of all keypairs

    keypairs is a list that will be filled in with the keypairs
    """
    return ctorProgramRunner('ec2-describe-keypairs', lambda l : keypairs.append(l.split()[1]), log=log)

def listKeypairs(log=False):
    """
    Blocking version, returns a list of keypairs
    """
    keypairs = []
    runProgramRunnerEx(listKeypairsA(keypairs, log=log))
    return keypairs

def addKeypairA(name, log=False):
    return ctorProgramRunner('ec2-add-keypair ' + name, None, log=log)

def addKeypair(name, log=False):
    """
    Creates a keypair.

    Currently does not return anything
    """
    runProgramRunnerEx(addKeypairA(name, log=log))

def listGroupsA(groups, log=False):
    return ctorProgramRunner('ec2-describe-group',
                             lambda l : l.startswith('GROUP') and groups.append(tuple(l.strip().split('\t', 3)[2:])))

def listGroups(log=False):
    """
    Blocking versino, returns a list of groups that exit.

    Right now this doesn't parse the rules of a group. A list of tuples is returned:
    [(group name, group description)]
    """
    groups = []
    runProgramRunnerEx(listGroupsA(groups, log=log))
    return groups

def addGroupA(name, description, log=False):
    return ctorProgramRunner('ec2-add-group %s -d "%s"' % (name, description), None, log=log)
        
def addGroup(name, description, log=False):
    """
    Blocking version, creates a group
    """
    runProgramRunnerEx(addGroupA(name, description, log=log))



def authorizeGroupA(groupName,
                    protocol,
                    portRange,
                    sourceGroup,
                    sourceGroupUser,
                    sourceSubnet,
                    log=False):
    
    cmd = ['ec2-authorize',
           groupName,
           '-P ' + protocol,
           ]

    
    if protocol == 'icmp':
        cmd.append('-t %d:%d' % (portRange[0], portRange[1]))
    else:
        try:
            portRange = str(portRange[0]) + '-' + str(portRange[1])
        except:
            portRange = str(portRange)
        cmd.append('-p ' + portRange)

    if sourceGroup:
        cmd.append('-o ' + sourceGroup)

    if sourceGroupUser:
        cmd.append('-u ' + sourceGroupUser)

    if sourceSubnet:
        cmd.append('-s ' + sourceSubnet)

    return ctorProgramRunner(' '.join(cmd), None, log=log)

    
def authorizeGroup(groupName,
                   protocol,
                   portRange,
                   sourceGroup=None,
                   sourceGroupUser=None,
                   sourceSubnet=None,
                   log=False):
    runProgramRunnerEx(authorizeGroupA(groupName,
                                       protocol,
                                       portRange,
                                       sourceGroup,
                                       sourceGroupUser,
                                       sourceSubnet, log=log))

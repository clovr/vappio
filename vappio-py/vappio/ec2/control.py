##
# This has functions wrapping ec2 functionality.  This is currently implemented
# by wrapping the ec2-api tools binaries but it could be replaced by something like Boto.
# The reason binaries are being wrapped here is because the nimbus clouds require a specific
# version of the tools and it would be easier to use a single code-base for controlling thigns
# with EC2 (the nimbus stuff can just call this).  For that reason, the ec2-bins are wrapped
# otherwise we could get into a situationw here Boto implements one version of the tools and
# it does not work on NIMBUS but on ec2 or vice versa.
import os

from igs.utils import logging
from igs.utils.logging import errorPrint
from igs.utils.commands import runProgramRunnerEx, ProgramRunner
from igs.utils import functional

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
                 monitor,
                 spotRequestId,
                 bidPrice):

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
        self.spotRequestId = spotRequestId
        self.bidPrice = bidPrice

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
                                self.monitor,
                                self.spotRequestId,
                                self.bidPrice),)


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
                monitor=instance.monitor,
                spotRequestId=instance.spotRequestId,
                bidPrice=instance.bidPrice)

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
                    d['monitor'],
                    d['spotRequestId'],
                    d['bidPrice'])

    
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
                            monitor,
                            ## Ignoring spot instance stuff for right now
                            None,
                            None)
        except ValueError:
            errorPrint('Failed to parse line: ' + line)
            return None
    elif line.startswith('SPOTINSTANCEREQUEST'):
        try:
            sline = line.split('\t')
            _, sir, bid, sType, _arch, _active, _time, _1, _2, _3, _4, instanceId, amiId, iType, key = sline[:15]
            return Instance(instanceId,
                            amiId,
                            None,
                            None,
                            None,
                            key,
                            None,
                            iType,
                            None,
                            None,
                            None,
                            sir,
                            bid)
        except ValueError:
            errorPrint('Failed to parse line: ' + line)
            return None
    else:
        return None



def instantiateCredential(conf, cred):
    """
    Takes a credential and instanitates it.  It returns a Record that has all of the
    information users of that instantiated credential will need
    """
    certFile = os.path.join(conf('general.secure_tmp'), cred.name + '_cert.pem')
    keyFile = os.path.join(conf('general.secure_tmp'), cred.name + '_key.pem')
    if not os.path.exists(certFile) or open(certFile).read() != cred.cert:
        open(certFile, 'w').write(cred.cert)
    if not os.path.exists(keyFile) or open(keyFile).read() != cred.pkey:
        open(keyFile, 'w').write(cred.pkey)
    newCred = functional.Record(cert=certFile, pkey=keyFile, ec2URL=None)
    if 'ec2_url' in cred.metadata:
        return newCred.update(ec2URL=cred.metadata['ec2_url'])
    else:
        return newCred

def addCredInfo(cmd, cred):
    cmd.extend(['-K', cred.pkey, '-C', cred.cert])
    if cred.ec2URL:
        cmd.extend(['-U', cred.ec2URL])
    
def runInstancesA(cred,
                  instances,
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

    addCredInfo(cmd, cred)

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

def runInstances(cred, *args, **kwargs):
    """Blocking version of runInstancesA, this returns a list of instances"""
    instances = []
    runProgramRunnerEx(runInstancesA(cred, instances, *args, **kwargs))
    return instances

def runSpotInstancesA(cred,
                      instances,
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
    """
    instances - a list that will be populated with the running instances - weak sauce, work on fixing this
    bidPrice - Maximum bid price for a spot instance
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
    cmd = ['ec2-request-spot-instances',
           amiId,
           '--price ' + str(bidPrice),
           '--type one-time',
           '-k ' + key,
           '--instance-type ' + instanceType]

    addCredInfo(cmd, cred)
    
    if availabilityZone:
        cmd.append('-z %s' % availabilityZone)

    ##
    # add groups
    for g in groups:
        cmd.append('--group ' +  g)

    if number:
        cmd.append('--instance-count %d ' % number)

    if userData:
        cmd.append('-d ' + userData)

    if userDataFile:
        cmd.append('-f ' + userDataFile)

    return ctorProgramRunner(' '.join(cmd), _instanceParse, log=log)

def runSpotInstances(cred, *args, **kwargs):
    """Blocking version of runSpotInstancesA, this returns a list of instances"""
    instances = []
    runProgramRunnerEx(runSpotInstancesA(cred, instances, *args, **kwargs))
    return instances

def listInstancesA(cred, instances, log=False):
    """List all currently running instances"""
    def _instanceParse(line):
        instance = parseInstanceLine(line)
        if instance:
            instances.append(instance)

    cmd = ['ec2-describe-instances']
    addCredInfo(cmd, cred)
    return ctorProgramRunner(' '.join(cmd), _instanceParse, log=log)

def listInstances(cred, log=False):
    """Blocking version, returns list of instances"""
    instances = []
    runProgramRunnerEx(listInstancesA(cred, instances, log=log))
    return instances
                 
def terminateInstancesA(cred, instances, log=False):
    """Asynchronous, terminate all instances that match the filter function"""
    cmd = ['ec2-terminate-instances']
    addCredInfo(cmd, cred)
    cmd.extend([i.instanceId for i in instances])
    return ctorProgramRunner(' '.join(cmd), log=log)

def terminateInstances(cred, instances, log=False):
    runProgramRunnerEx(terminateInstancesA(cred, instances, log=log))
    
    
def updateInstancesA(cred, retInst, instances, log=False):
    """
    Updates the list of states of the instances given.

    retInst - List that will be filled with values of the new instances
    instances - List of instances that should be updated
    """

    instanceSet = set([i.instanceId for i in instances if i.instanceId and not i.spotRequestId])
    spotRequestSet = set([i.spotRequestId for i in instances if i.spotRequestId])
    spotInstanceSet = set()
    spotInstances = []
    
    def _instanceParse(line):
        instance = parseInstanceLine(line)
        if instance and (instance.instanceId and instance.instanceId in instanceSet or
            instance.spotRequestId and instance.spotRequestId in spotRequestSet):
            
            
            if not instance.instanceId and instance.spotRequestId:
                retInst.append(instance)
            elif instance.instanceId and instance.spotRequestId:
                spotInstanceSet.add(instance.instanceId)
                instanceSet.add(instance.instanceId)
                spotInstances.append(instance)
            elif instance.instanceId in spotInstanceSet:
                idx = functional.find(lambda i: i.instanceId == instance.instanceId, spotInstances)
                t = spotInstances[idx]
                instance.spotRequestId = t.spotRequestId
                instance.bidPrice = t.bidPrice
                retInst.append(instance)
            elif instance.instanceId in instanceSet:
                retInst.append(instance)                

    ##
    # First determine if any of these are spot instances without an instance type associated
    spotRequests = [i for i in instances if i.spotRequestId]
    ##
    # If there are unfulfilled spot requests then update spot instance list so we can update
    # a running instance with the request information
    if spotRequests:
        cmd = ['ec2-describe-spot-instance-requests']
        addCredInfo(cmd, cred)
        cmd.extend([';', 'ec2-describe-instances'])
    else:
        cmd = ['ec2-describe-instances']

    addCredInfo(cmd, cred)        
    return ctorProgramRunner(' '.join(cmd), _instanceParse, log=log)


def updateInstances(cred, instances, log=False):
    retInst = []
    runProgramRunnerEx(updateInstancesA(cred, retInst, instances, log=log))
    return retInst

def listKeypairsA(cred, keypairs, log=False):
    """
    Returns a list of all keypairs

    keypairs is a list that will be filled in with the keypairs
    """
    cmd = ['ec2-describe-keypairs']
    addCredInfo(cmd, cred)
    return ctorProgramRunner(' '.join(cmd), lambda l : keypairs.append(l.split()[1]), log=log)

def listKeypairs(cred, log=False):
    """
    Blocking version, returns a list of keypairs
    """
    keypairs = []
    runProgramRunnerEx(listKeypairsA(cred, keypairs, log=log))
    return keypairs

def addKeypairA(cred, name, log=False):
    cmd = ['ec2-add-keypair']
    addCredInfo(cmd, cred)
    cmd.append(name)
    return ctorProgramRunner(' '.join(cmd), None, log=log)

def addKeypair(cred, name, log=False):
    """
    Creates a keypair.

    Currently does not return anything
    """
    runProgramRunnerEx(addKeypairA(cred, name, log=log))

def listGroupsA(cred, groups, log=False):
    cmd = ['ec2-describe-group']
    addCredInfo(cmd, cred)
    return ctorProgramRunner(' '.join(cmd),
                             lambda l : l.startswith('GROUP') and groups.append(tuple(l.strip().split('\t', 3)[2:])))

def listGroups(cred, log=False):
    """
    Blocking versino, returns a list of groups that exit.

    Right now this doesn't parse the rules of a group. A list of tuples is returned:
    [(group name, group description)]
    """
    groups = []
    runProgramRunnerEx(listGroupsA(cred, groups, log=log))
    return groups

def addGroupA(cred, name, description, log=False):
    cmd = ['ec2-add-group']
    addCredInfo(cmd, cred)
    cmd.extend([name, '-d', '"' + description + '"'])
    return ctorProgramRunner(' '.join(cmd), None, log=log)
        
def addGroup(cred, name, description, log=False):
    """
    Blocking version, creates a group
    """
    runProgramRunnerEx(addGroupA(cred, name, description, log=log))



def authorizeGroupA(cred,
                    groupName,
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

    addCredInfo(cmd, cred)
    
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

    
def authorizeGroup(cred,
                   groupName,
                   protocol,
                   portRange,
                   sourceGroup=None,
                   sourceGroupUser=None,
                   sourceSubnet=None,
                   log=False):
    runProgramRunnerEx(authorizeGroupA(cred,
                                       groupName,
                                       protocol,
                                       portRange,
                                       sourceGroup,
                                       sourceGroupUser,
                                       sourceSubnet, log=log))

##
# This has functions wrapping ec2 functionality.  This is currently implemented
# by wrapping the ec2-api tools binaries but it could be replaced by something like Boto.
# The reason binaries are being wrapped here is because the nimbus clouds require a specific
# version of the tools and it would be easier to use a single code-base for controlling thigns
# with EC2 (the nimbus stuff can just call this).  For that reason, the ec2-bins are wrapped
# otherwise we could get into a situationw here Boto implements one version of the tools and
# it does not work on NIMBUS but on ec2 or vice versa.
import sets


from igs.utils import logging
from igs.utils.logging import logPrint, debugPrint
from igs.utils.commands import runSystemEx, runSingleProgram, runProgramRunnerEx, ProgramRunner


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
    
def ctorProgramRunner(cmd, stdoutf=logging.OUTSTREAM.write, stderrf=logging.ERRSTREAM.write, log=False):
    return ProgramRunner(cmd, stdoutf, stderrf, log=log)


def parseInstanceLine(line):
    if line.startswith('INSTANCE'):
        _, instanceId, amiId, pubDns, privDns, state, key, index, _unsure, t, launch, zone, monitor = line.strip().split('\t')

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
    else:
        return None



def runInstancesA(instances,
                  amiId,
                  key,
                  instanceType,
                  groups,
                  availabilityZone,
                  number=None,
                  userData=None,
                  userDataFile=None):
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
    cmd = 'ec2-run-instances %s -k %s -t %s -z %s ' % (amiId, key, instanceType, availabilityZone)

    ##
    # add groups
    for g in groups:
        cmd += '-g %s ' % g

    if number:
        cmd += '-n %d ' % number

    if userData:
        cmd += '-d %s ' % userData

    if userDataFile:
        cmd += '-f %s ' % userDataFile

    return ctorProgramRunner(cmd, _instanceParse, log=True)

def runInstances(*args, **kwargs):
    """Blocking version of runInstancesA, this returns a list of instances"""
    instances = []
    runProgramRunnerEx(runInstancesA(instances, *args, **kwargs))
    return instances

def listInstancesA(instances):
    """List all currently running instances"""
    def _instanceParse(line):
        instance = parseInstanceLine(line)
        if instance:
            instances.append(instance)

    return ctorProgramRunner('ec2-describe-instances', _instanceParse, log=True)

def listInstances():
    """Blocking version, returns list of instances"""
    instances = []
    runProgramRunnerEx(listInstancesA(instances))
    return instances
                 
def terminateInstancesA(instances):
    """Asynchronous, terminate all instances that match the filter function"""
    return ctorProgramRunner('ec2-terminate-instances ' + ' '.join([i.instanceId for i in instances]), log=True)

def terminateInstances(instances):
    runProgramRunnerEx(terminateInstancesA(instances))
    
    
def updateInstancesA(retInst, instances):
    """
    Updates the list of states of the instances given.

    retInst - List that will be filled with values of the new instances
    instances - List of instances that should be updated
    """

    instanceSet = sets.Set([i.instanceId for i in instances])

    def _instanceParse(line):
        instance = parseInstanceLine(line)
        if instance and instance.instanceId in instanceSet:
            retInst.append(instance)


    return ctorProgramRunner('ec2-describe-instances', _instanceParse, log=True)


def updateInstances(instances):
    retInst = []
    runProgramRunnerEx(updateInstancesA(retInst, instances))
    return retInst

            

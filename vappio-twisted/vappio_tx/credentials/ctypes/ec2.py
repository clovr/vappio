##
# This has functions wrapping ec2 functionality.  This is currently implemented
# by wrapping the ec2-api tools binaries but it could be replaced by something like Boto.
# The reason binaries are being wrapped here is because the nimbus clouds require a specific
# version of the tools and it would be easier to use a single code-base for controlling things
# with EC2 (the nimbus stuff can just call this).  For that reason, the ec2-bins are wrapped
# otherwise we could get into a situationw here Boto implements one version of the tools and
# it does not work on NIMBUS but on ec2 or vice versa.
import os

from twisted.internet import defer

from igs_tx.utils import commands

from igs.utils import logging
from igs.utils import functional
from igs.utils import config

##
# This module wants to go by
NAME = 'EC2'
DESC = """Control module for EC2"""

DEFAULT_CONFIG_FILE = '/mnt/vappio-conf/clovr_ec2.conf'

class Instance(functional.Record):
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
    return dict(instance_id=instance.instanceId,
                ami_id=instance.amiId,
                public_dns=instance.publicDNS,
                private_dns=instance.privateDNS,
                state=instance.state,
                key=instance.key,
                index=instance.index,
                instance_type=instance.instanceType,
                launch=instance.launch,
                availability_zone=instance.availabilityZone,
                monitor=instance.monitor,
                spot_request_id=instance.spotRequestId,
                bid_price=instance.bidPrice)

def instanceFromDict(d):
    return Instance(d['instance_id'],
                    d['ami_id'],
                    d['public_dns'],
                    d['private_dns'],
                    d['state'],
                    d['key'],
                    d['index'],
                    d['instance_type'],
                    d['launch'],
                    d['availability_zone'],
                    d['monitor'],
                    d['spot_request_id'],
                    d['bid_price'])

    

def addCredInfo(cmd, cred):
    # Copy cmd since we'll be modifying it
    cmd = list(cmd)
    cmdName = cmd.pop(0)
    credOptions = []
    credOptions.extend(['-K', cred.pkey, '-C', cred.cert])
    # if cred.ec2URL:
    #     credOptions.extend(['-U', cred.ec2URL])
    return [cmdName] + credOptions + cmd

def runWithCred(cred, cmd, stdoutf=logging.OUTSTREAM.write, stderrf=logging.ERRSTREAM.write, log=False):
    cmdPrefix = ''
    if hasattr(cred, 'ec2Path'):
        cmdPrefix = cred.ec2Path + '/'

    cmd = addCredInfo(cmd, cred)
    cmd[0] = cmdPrefix + cmd[0]
    return commands.runProcess(cmd, stdoutf=stdoutf, stderrf=stderrf, log=log, addEnv=cred.env)

def run(cred, cmd, log=False):
    stdout = []
    stderr = []
    d = runWithCred(cred, cmd, stdoutf=stdout.append, stderrf=stderr.append, log=log)

    def _joinStdout(_exitCode):
        return ''.join(stdout).splitlines()

    d.addCallback(_joinStdout)

    def _errBack(_f):
        raise commands.ProgramRunError(cmd, ''.join(stderr))

    d.addErrback(_errBack)

    return d
    
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
            logging.errorPrint('Failed to parse line: ' + line)
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
            logging.errorPrint('Failed to parse line: ' + line)
            return None
    else:
        return None



def fixTypesOfSelectConfig(conf):
    return config.configFromMap({'cluster.master_groups': [g for g in conf('cluster.master_groups').split(',') if g],
                                 'cluster.exec_groups': [g for g in conf('cluster.exec_groups').split(',') if g]},
                                base=conf)
    
def instantiateCredential(conf, cred):
    """
    Takes a credential and instanitates it.  It returns a Record that has all of the
    information users of that instantiated credential will need
    """
    if not conf('config_loaded', default=False):
        conf = config.configFromStream(open(conf('general.conf_file', default=DEFAULT_CONFIG_FILE)), base=conf)
    conf = fixTypesOfSelectConfig(conf)
    certFile = os.path.join(conf('general.secure_tmp'), cred.name + '_cert.pem')
    keyFile = os.path.join(conf('general.secure_tmp'), cred.name + '_key.pem')
    if not os.path.exists(certFile) or open(certFile).read() != cred.cert:
        open(certFile, 'w').write(cred.cert)
    if not os.path.exists(keyFile) or open(keyFile).read() != cred.pkey:
        open(keyFile, 'w').write(cred.pkey)
    newCred = functional.Record(name=cred.name, conf=conf, cert=certFile, pkey=keyFile, ec2URL=None, env={})
    if 'ec2_url' in cred.metadata:
        return defer.succeed(newCred.update(env=functional.updateDict(newCred.env,
                                                                      dict(EC2_URL=cred.metadata['ec2_url']))))
    else:
        return defer.succeed(newCred)

    
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
    
    ##
    # make base command
    cmd = ['ec2-run-instances',
           amiId,
           '-k', key,
           '-t', instanceType]

    if availabilityZone:
        cmd.extend(['-z', availabilityZone])

    ##
    # add groups
    for g in groups:
        cmd.extend(['-g', g])

    if number:
        cmd.extend(['-n',  str(number)])

    if userData:
        cmd.extend(['-d', userData])

    if userDataFile:
        cmd.extend(['-f', userDataFile])

    d = run(cred, cmd, log=log)

    def _parseInstances(lines):
        instances = []
        for line in lines:
            instance = parseInstanceLine(line)
            if instance:
                instances.append(instance)

        return instances

    d.addCallback(_parseInstances)
    return d

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
    ##
    # make base command
    cmd = ['ec2-request-spot-instances',
           amiId,
           '--price', str(bidPrice),
           '--type', 'one-time',
           '-k', key,
           '--instance-type', instanceType]

    if availabilityZone:
        cmd.extend(['-z', availabilityZone])

    ##
    # add groups
    for g in groups:
        cmd.extend(['--group',  g])

    if number:
        cmd.extend(['--instance-count', str(number)])

    if userData:
        cmd.extend('-d ' + userData)

    if userDataFile:
        cmd.extend(['-f', userDataFile])

    d = run(cred, cmd, log=log)

    def _parseInstances(lines):
        instances = []
        for line in lines:
            instance = parseInstanceLine(line)
            if instance:
                instances.append(instance)

        return instances

    d.addCallback(_parseInstances)
    return d


def listInstances(cred, log=False):
    """List all currently running instances"""
    cmd = ['ec2-describe-instances']

    d = run(cred, cmd, log=log)

    def _parseInstances(lines):
        instances = []
        for line in lines:
            instance = parseInstanceLine(line)
            if instance:
                instances.append(instance)

        return instances

    d.addCallback(_parseInstances)
    return d

def terminateInstances(cred, instances, log=False):
    """Terminate all instances that match the filter function"""
    cmd = ['ec2-terminate-instances']
    cmd.extend([i.instanceId for i in instances])
    d = run(cred, cmd, log=log)
    unfilledSpotInstances = [i.spotRequestId for i in instances if not i.instanceId and i.spotRequestId]
    if unfilledSpotInstances:
        d.addCallback(lambda _ : run(cred, ['ec2-cancel-spot-instance-requests'] + unfilledSpotInstances, log=log))

    return d

def updateInstances(cred, instances, log=False):
    """
    Updates the list of states of the instances given.

    retInst - List that will be filled with values of the new instances
    instances - List of instances that should be updated
    """


    retInst = []
    def _instanceParse(lines):
        instanceSet = set([i.instanceId for i in instances if i.instanceId and not i.spotRequestId])
        spotRequestSet = set([i.spotRequestId for i in instances if i.spotRequestId])
        spotInstanceSet = set()
        spotInstances = []

        for line in lines:
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

        return retInst

    ##
    # First determine if any of these are spot instances
    spotRequests = [i for i in instances if i.spotRequestId]
    ##
    # If there are unfulfilled spot requests then update spot instance list so we can update
    # a running instance with the request information
    if spotRequests:
        d = run(cred, ['ec2-describe-spot-instance-requests'], log=log)
        d.addCallback(_instanceParse)
        d.addCallback(lambda _ : run(cred, ['ec2-describe-instances'], log=log))
        d.addCallback(_instanceParse)
    else:
        d = run(cred, ['ec2-describe-instances'], log=log)
        d.addCallback(_instanceParse)
        
    return d


def listKeypairs(cred, log=False):
    """
    Returns a list of all keypairs

    keypairs is a list that will be filled in with the keypairs
    """
    cmd = ['ec2-describe-keypairs']
    d = run(cred, cmd, log=log)
    d.addCallback(lambda ls : [l.split()[1] for l in ls])
    return d

def addKeypair(cred, name, log=False):
    cmd = ['ec2-add-keypair', name]
    return run(cred, cmd, log=log)

def listGroups(cred, log=False):
    cmd = ['ec2-describe-group']
    d = run(cred, cmd, log=log)
    d.addCallback(lambda ls : [tuple(l.strip().split('\t', 3)[2:])
                               for l in ls
                               if l.startswith('GROUP')])
    return d

def addGroup(cred, name, description, log=False):
    cmd = ['ec2-add-group', name, '-d', '"' + description + '"']
    return run(cred, cmd, log=log)
        

def authorizeGroup(cred,
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
    
    if protocol == 'icmp':
        cmd.extend(['-t', '%d:%d' % (portRange[0], portRange[1])])
    else:
        try:
            portRange = str(portRange[0]) + '-' + str(portRange[1])
        except:
            portRange = str(portRange)
        cmd.extend(['-p', portRange])

    if sourceGroup:
        cmd.extend(['-o', sourceGroup])

    if sourceGroupUser:
        cmd.extend(['-u', sourceGroupUser])

    if sourceSubnet:
        cmd.extend(['-s',  sourceSubnet])

    return run(cred, cmd, log=log)


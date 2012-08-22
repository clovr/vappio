import os
import sys

import pymongo

from twisted.internet import defer
from twisted.internet import threads

from igs.utils import functional as func
from igs.utils import config

from vappio_tx.credentials.ctypes import ec2 as ec2control

from vappio_tx.www_client import clusters as clusters_www

"""Control module for imported clusters"""

##
# This module wants to go by
NAME = 'adhoc'
DESC = """Control module for imports, mostly NOOPs"""

DEFAULT_CONFIG_FILE = '/mnt/vappio-conf/clovr.conf'

##
# Look just like EC2's instance
Instance = ec2control.Instance
instanceToDict = ec2control.instanceToDict
instanceFromDict = ec2control.instanceFromDict

def instantiateCredential(conf, cred):
    """Instantiates a credential based off the configuration provided."""
    if 'conf_file' not in conf or not conf('conf_file'):
        conf = config.configFromMap({'conf_file': DEFAULT_CONFIG_FILE}, 
                                    base=conf)    

    newCred = func.Record(name=cred.name, conf=conf)
    return defer.succeed(newCred)

def runInstances(cred, *args, **kwargs):
    return defer.succeed([])

def runSpotInstances(cred, *args, **kwargs):
    return defer.succeed([])

def listInstances(cred, log=False):
    """Returns a list of all running instances attached to the provided 
    credential.

    Because adhoc credentials will be associated with clusters/instances that 
    span multiple VM's/hosts an easy method to retrieve all instances and their
    current state does not exist.  

    Each cluster associated with this credential will need to be queried 
    to pull down all of its instances and their current state
    
    """
    @defer.inlineCallbacks
    def _parseInstances(importedClusters):
        """Parses out all instances associated with this cluster."""
        instances = []
        
        # List of things to do here to make this work
        #
        #   1.) Pull down all the clusters associated with this cred
        #   2.) Check if each cred has a master, if it doesn't we don't care
        #   3.) If a master exists check its state, needs to be in running state
        #   4.) For each running master retrieve the public DNS and shoot off 
        #       a request to its list clusters WWW
        #   5.) Parse returned instances for those in running state

        # TODO: Put in place all our authorization junk
        for cluster in importedClusters:
            master = cluster.get('master')

            if master and master.get('state') == 'running':
                # TODO: We have no guarantee that the imported cluster name 
                #       will be the same as the remote cluster name. Need to 
                #       have some other attribute that contains this information
                remoteClusters = yield clusters_www.listClusters(master.get('public_dns'),
                                                                 #{'cluster_name': cluster.get('cluster_name')},
                                                                 {'cluster_name': 'local'},
                                                                 cluster.get('user_name'))
                remoteCluster = remoteClusters[0]
                instances.extend([instanceFromDict(x) for x 
                                  in [remoteCluster.get('master'), remoteCluster.get('exec_nodes')] 
                                  if x and x.get('state') == 'running'])

        defer.returnValue(instances)

    d = threads.deferToThread(lambda : pymongo.Connection().clovr.clusters.find(dict(cred_name=cred.name)))
    d.addCallback(_parseInstances)
    return d

def updateInstances(cred, instances, log=False):
    """Updates the list of states of the instances given. 

    Because adhoc credentials will be associated with clusters/instances that 
    span multiple VM's/hosts an easy method to retrieve all instances and their
    current state does not exist. 

    Instances and their states will need to be retrieved from each respective 
    host.

    retInst - List that will be filled with values of the new instances
    instances - List of instances that should be updated.

    """

    retInst = []

    @defer.inlineCallbacks
    def _parseInstances(importedClusters):
        """Parses out all instances associated with this cluster."""
 
        # List of things to do here to make this work
        #
        #   1.) Pull down all the clusters associated with this cred
        #   2.) Check if each cred has a master, if it doesn't we don't care
        #   3.) If a master exists check its state, needs to be in running state
        #   4.) For each running master retrieve the public DNS and shoot off 
        #       a request to its list clusters WWW
        #   5.) Parse returned instances for those in running state

        # TODO: Put in place all our authorization junk
        for cluster in importedClusters:
            master = cluster.get('master')

            if master and cluster.get('state') == 'running':
                # TODO: We have no guarantee that the imported cluster name 
                #       will be the same as the remote cluster name. Need to 
                #       have some other attribute that contains this information
                remoteClusters = yield clusters_www.listClusters(master.get('public_dns'),
                                                                {'cluster_name': cluster.get('cluster_name')},
                                                                cluster.get('user_name'),
                                                                None,
                                                                timeout=10,
                                                                tries=3)
                remoteCluster = remoteClusters[0]
                retInst.extend([instanceFromDict(x) for x 
                                in [remoteCluster.get('master'), remoteCluster.get('exec_nodes')] 
                                if x and x.get('instance_id') in instances])

        defer.returnValue(retInst)

    d = threads.deferToThread(lambda : pymongo.Connection().clovr.clusters.find(dict(cred_name=cred.name)))
    d.addCallback(_parseInstances)
    return d

def terminateInstances(cred, instances, log=False):
    """Attempts to terminate the provided instances. 
    
    In the case of an adhoc
    cluster termination will only remove the provided instances from use on 
    the VM initiating the terminate instances calls.
    
    """
    return defer.succeed([])

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

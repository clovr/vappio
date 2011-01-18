import json

from twisted.internet import defer

from igs.utils import functional as func
from igs.utils import config

from vappio_tx.utils import queue

from vappio_tx.www_client import credentials

def performQuery(mq, queryQueue, request):
    retQueue = queue.randomQueueName('credentials')
    d = defer.Deferred()
    
    def _handleMsg(mq, m):
        mq.unsubscribe(retQueue)
        ret = json.loads(m.body)
        if ret['success']:
            return d.callback(ret['data'])
        else:
            d.errback(queue.RemoteError(ret['data']['name'],
                                        ret['data']['msg'],
                                        ret['data']['stacktrace']))

    mq.subscribe(_handleMsg, retQueue)
    mq.send(queryQueue, json.dumps(func.updateDict(request, {'return_queue': retQueue})))
    return d

class CredentialClient:
    def __init__(self, credName, messageQueue, conf):
        self.credName = credName
        self.mq = messageQueue
        self.conf = conf


    def credentialConfig(self):
        query = dict(credential_name=self.credName)
        return performQuery(self.mq,
                            self.conf('credentials.credentialconfig_queue'),
                            query)
    
    def runInstances(self,
                     ami,
                     key,
                     instanceType,
                     groups,
                     availabilityZone=None,
                     numInstances=1,
                     userData=None,
                     userDataFile=None):
        query = dict(credential_name=self.credName,
                     ami=ami,
                     key=key,
                     instance_type=instanceType,
                     groups=groups,
                     availability_zone=availabilityZone,
                     num_instances=numInstances,
                     user_data=userData,
                     user_data_file=userDataFile)
        return performQuery(self.mq,
                            self.conf('credentials.runinstances_queue'),
                            query)
    

    def runSpotInstances(self,
                         bidPrice,
                         ami,
                         key,
                         instanceType,
                         groups,
                         availabilityZone=None,
                         numInstances=1,
                         userData=None,
                         userDataFile=None):
        query = dict(credential_name=self.credName,
                     ami=ami,
                     bid_price=bidPrice,
                     key=key,
                     instance_type=instanceType,
                     groups=groups,
                     availability_zone=availabilityZone,
                     num_instances=numInstances,
                     user_data=userData,
                     user_data_file=userDataFile)
        return performQuery(self.mq,
                            self.conf('credentials.runspotinstances_queue'),
                            query)
    
    
    def listInstances(self):
        query = dict(credential_name=self.credName)
        return performQuery(self.mq,
                            self.conf('credentials.listinstances_queue'),
                            query)

    
    def updateInstances(self, instances):
        query = dict(credential_name=self.credName,
                     instances=instances)
        return performQuery(self.mq,
                            self.conf('credentials.updateinstances_queue'),
                            query)
    
    def terminateInstances(self, instances):
        query = dict(credential_name=self.credName,
                     instances=instances)
        return performQuery(self.mq,
                            self.conf('credentials.terminateinstances_queue'),
                            query)

    def listKeypairs(self):
        query = dict(credential_name=self.credName)
        return performQuery(self.mq,
                            self.conf('credentials.listkeypairs_queue'),
                            query)

    def addKeypair(self, keypairName):
        query = dict(credential_name=self.credName,
                     keypair_name=keypairName)
        return performQuery(self.mq,
                            self.conf('credentials.addkeypairs_queue'),
                            query)        

    def listGroups(self):
        query = dict(credential_name=self.credName)
        return performQuery(self.mq,
                            self.conf('credentials.listgroups_queue'),
                            query)

    def addGroup(self, groupName, groupDescription):
        query = dict(credential_name=self.credName,
                     group_name=groupName,
                     group_description=groupDescription)
        return performQuery(self.mq,
                            self.conf('credentials.addgroup_queue'),
                            query)

    def authorizeGroup(self,
                       groupName,
                       protocol,
                       portRange,
                       sourceGroup=None,
                       sourceGroupUser=None,
                       sourceSubnet=None):
        query = dict(credential_name=self.credName,
                     group_name=groupName,
                     protocol=protocol,
                     port_range=portRange,
                     source_group=sourceGroup,
                     source_group_user=sourceGroupUser,
                     source_subnet=sourceSubnet)
        return performQuery(self.mq,
                            self.conf('credentials.authorizegroup_queue'),
                            query)        
    
    

def saveCredential(credName, description, ctype, cert, pkey, metadata, conf):
    return credentials.saveCredential('localhost',
                                      'local',
                                      credName,
                                      description,
                                      ctype,
                                      cert,
                                      pkey,
                                      metadata,
                                      config.configToDict(conf))


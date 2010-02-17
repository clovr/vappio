#!/usr/bin/env python
import os
import json

from igs.utils.core import getStrBetween
from igs.utils.config import configFromEnv, configFromMap, configFromStream
from igs.cgi.handler import CGIPage, generatePage

from vappio.cluster.control import Cluster
from vappio.cluster.misc import getInstances
from vappio.cluster.persist_mongo import load, dump, ClusterDoesNotExist

from vappio.ec2 import control as ec2control

class ClusterInfo(CGIPage):

    def body(self):
        options = configFromEnv()
        try:
            cluster = load('local')
        except ClusterDoesNotExist:
            options = configFromStream(open('/tmp/machine.conf'), options)
            options = configFromMap({'general': {'ctype': 'ec2'},
                                     'cluster': {'master_groups': [f.strip() for f in options('cluster.master_groups').split(',')],
                                                 'exec_groups': [f.strip() for f in options('cluster.exec_groups').split(',')]
                                                 }
                                     },
                                    options)
            cluster = Cluster('local', ec2control, options)
            cluster.setMaster(getInstances(lambda i : i.privateDNS == cluster.config('MASTER_IP'), ec2control)[0])



        return json.dumps([True, {'execNodes': [i.publicDNS for i in cluster.execNodes],
                                  'dataNodes': [i.publicDNS for i in cluster.dataNodes]}])
                           
        
        
generatePage(ClusterInfo())

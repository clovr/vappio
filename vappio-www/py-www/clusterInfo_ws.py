#!/usr/bin/env python
import os
import json

from igs.utils.core import getStrBetween
from igs.utils.config import configFromEnv
from igs.cgi.handler import CGIPage, generatePage

from vappio.pipeline_tools.persist import load, loadAll

from vappio.cluster.persist import load, dump, ClusterDoesNotExist

class ClusterInfo(CGIPage):

    def body(self):
        conf = configFromEnv()

        try:
            cluster = load(os.path.join(options('env.VAPPIO_HOME'), 'db'), 'local')
        except ClusterDoesNotExist:
            options = configFromMap({'general': {'ctype': 'ec2'}},
                                    configFromStream(open('/tmp/machine.conf'),
                                                     configFromEnv(options)))
            cluster = Cluster('local', ec2control, options)
            cluster.setMaster(getInstances(lambda i : i.privateDNS == cluster.config('MASTER_IP'), ec2control)[0])



        return json.dumps([True, {'execNodes': [i.publicDNS for i in cluster.execNodes],
                                  'dataNodes': [i.publicDNS for i in cluster.dataNodes]}])
                           
        
        
generatePage(ClusterInfo())

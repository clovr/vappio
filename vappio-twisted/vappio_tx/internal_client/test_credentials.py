from twisted.application import service
from twisted.python import log

from igs.utils import config

from vappio_tx.mq import client
from vappio_tx.internal_client import credentials


conf = config.configFromStream(open('/mnt/vappio-conf/vappio_apps.conf'))

application = service.Application('test')

s1 = client.makeService(conf)
s1.setServiceParent(application)

cc = credentials.CredentialClient('diag', s1.mqFactory, conf)

d = cc.listInstances()

def _terminate(instances):
    print 'Num instances:', len(instances)
    instances = instances[:3]
    print 'Shutting down: ', instances
    return cc.terminateInstances(instances)

def _print(foo):
    print 'Foo:', foo

d.addCallback(_terminate)
d.addCallback(_print)
d.addErrback(log.err)


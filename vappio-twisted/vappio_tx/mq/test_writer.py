from twisted.internet import reactor
from twisted.application import service

from twisted.internet import task

from igs.utils import config

from vappio_tx.mq import client

conf = config.configFromMap({'mq.username': '',
                             'mq.password': '',
                             'mq.host': 'localhost',
                             'mq.port': 61613})



application = service.Application('test')

s1 = client.makeService(conf)
s1.setServiceParent(application)

def loopingCall():
    lc = task.LoopingCall(lambda : s1.mqFactory.send('/queue/inbox', 'foo', {'ack-timeout': 60}))
    lc.start(0)

reactor.callLater(1, loopingCall)

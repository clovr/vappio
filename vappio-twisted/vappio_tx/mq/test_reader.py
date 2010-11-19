from twisted.internet import reactor
from twisted.application import service

from twisted.internet import task

from igs.utils import config

from vappio_tx.mq import client


def printIt(mq, m):
    print 'ACK', m.headers['message-id']
    print m.body
    mq.ack(m.headers['message-id'], headers={})

conf = config.configFromMap({'username': '',
                             'password': '',
                             'host': 'localhost',
                             'port': 61613})



application = service.Application('test')

s2 = client.makeService(conf)
s2.setServiceParent(application)
s2.mqFactory.subscribe(lambda m : printIt(s2.mqFactory, m), '/queue/inbox', {})

s1 = client.makeService(conf)
s1.setServiceParent(application)

def loopingCall():
    lc = task.LoopingCall(lambda : s1.mqFactory.send('/queue/inbox', {'ack-timeout': 60}, 'foo'))
    lc.start(0)

#reactor.callLater(1, loopingCall)

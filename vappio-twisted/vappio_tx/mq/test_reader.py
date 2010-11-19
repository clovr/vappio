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

s1 = client.makeService(conf)
s1.setServiceParent(application)
s1.mqFactory.subscribe(lambda m : printIt(s1.mqFactory, m), '/queue/inbox', {})


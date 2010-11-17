from igs.utils import config

from vappio_tx.mq import client

conf = config.configFromMap({'username': '',
                             'password': '',
                             'port': 61613})


def printFoo(
s = client.makeService(conf)
s.mqFactory.subscribe

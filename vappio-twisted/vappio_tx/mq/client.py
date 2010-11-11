#
# Message Queue client that will use stomper for backend.
#
# To use, call makeService with a config so it knows who to connect
# and any username password login information.

from zope import interface

from twisted.internet import protocol

import stomper

class MQClientProtocol(protocol.Protocol):

    ACTIONS = {'MESSAGE': lambda s, m : s.factory.msgReceived(m),
               'RECEIPT': lambda s, m : s.factory.receiptReceived(m),
               'ERROR': lambda s, m : s.factory.errorReceived(m),
               }
    
    def __init__(self):
        self.data = ''
        self.frames = []
    
    def connectionMade(self):
        pass

    def dataReceived(self, data):
        self.data += data

        (msg, remainingData) = stomper.unpack_frame()
        if msg is not None:
            self.ACTIONS[msg['cmd']](self, msg)
            self.data = remainingData


    def sendMessage(self, msg):
        self.transport.write(stomper.pack_frame(msg))

class IMQClientService(interface.Interface):
    """
    A message queue client
    """

    def subscribe(handler, destination, headers):
        """
        Subscribe to a queue or topic and us the list of headers given on it

        A deferred is returned, if success None is passed, if failure, the failure

        handler is a function that is called upon the incoming of a message
        """

    def unsubscribe(destination):
        """
        Unsubscribe form a destination
        """

    def send(destination, headers, body):
        """
        Send a message to the destination with the headers and the body.

        A deferred is returned, if success None is passed, if failure, the failure
        """

    def ack(messageId, headers):
        """
        Acknolwedge a message
        """

class IMQClientFactory(interface.Interface)
    """
    Factory for MQ client protocol
    """

    def buildProtocol(addr):
        """
        Return a protocol
        """

def makeService(config):
    pass


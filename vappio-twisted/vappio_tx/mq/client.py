#
# Message Queue client that will use stomper for backend.
#
# To use, call makeService with a config so it knows who to connect
# and any username password login information.

from zope import interface

from twisted.internet import protocol

import stomper

class IMQClientService(interface.Interface):
    """
    A message queue client
    """


    def connectedReceived(msg):
        """
        Client successfully connected
        """

    def msgReceived(msg):
        """
        Incoming message
        """

    def receiptReceived(msg):
        """
        Incoming receipt
        """

    def errorReceived(msg):
        """
        Incoming error
        """

class IMQClientFactory(interface.Interface)
    """
    Factory for MQ client protocol
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

    def connectionMade():
        """
        Called when the protocol is connected
        """
        
    def connectedReceived(msg):
        """
        Client successfully connected
        """

    def msgReceived(msg):
        """
        Incoming message
        """

    def receiptReceived(msg):
        """
        Incoming receipt
        """

    def errorReceived(msg):
        """
        Incoming error
        """


class MQClientProtocol(protocol.Protocol):

    ACTIONS = {'CONNECTED': lambda s, m : s.factory.connectedReceived(m),
               'MESSAGE': lambda s, m : s.factory.msgReceived(m),
               'RECEIPT': lambda s, m : s.factory.receiptReceived(m),
               'ERROR': lambda s, m : s.factory.errorReceived(m),
               }
    
    def __init__(self):
        self.data = ''
    
    def connectionMade(self):
        self.factory.connectionMade()

    def dataReceived(self, data):
        self.data += data

        (msg, remainingData) = stomper.unpack_frame()
        if msg is not None:
            self.ACTIONS[msg['cmd']](self, msg)
            self.data = remainingData


    def sendMessage(self, msg):
        self.transport.write(stomper.pack_frame(msg))


def transition(factory, newState):
    factory.state = newState(factory)

class _ConnectedState:
    def __init__(self, factory):
        self.factory = factory
        for handler, dst, headers in self.factory._subscriptions:
            self.factory.mqClient.sendMessage(stomper.subscribe(dst, ack='client', headers))

    def subscribe(handler, destination, headers):
        self.factory._subscriptions.append((handler, destination, headers))
        self.factory.mqClient.sendMessage(stomper.subscribe(dst, ack='client', headers))
        
    def unsubscribe(self, destination):
        #
        # Optimize later
        self.factory._removeSubscription(destination)

        self.factory.mqClient.sendMessage(stomper.unsubscribe(destination))

    def send(self, destination, headers, body):
        self.factory.mqClient.sendMessage(stomper.send(destination, body, headers))
        
    def ack(self, messageId, headers):
        self.factory.mqClient.sendMessage(stomper.ack(messageId, headers=headers))

    def msgReceived(self, msg):
        h = self.factory._findSubscription(msg.headers['destination'])
        if h:
            h(msg)
        else:
            raise Exception('Received message on unknown subscription')

    def receiptReceived(self, msg):
        raise Exception('Need to implement receipt')

    def errorReceived(self, msg):
        raise Exception('Need to implement error')

    
class _AuthenticatingState:
    def __init__(self, factory):
        self.factory = factory

    def connectedReceived(self, msg):
        self.factory.session = msg['session']

        transition(self.factory, _ConnectedState)

    def subscribe(self, handler, destination, headers):
        self.factory._subscriptions.append((handler, destination, headers))

class _ConnectingState:
    def __init__(self, factory):
        self.factory = factory
        
    def connectionMade(self):
        self.factory.mqClient.sendMessage(stomper.connect(self.factory.username,
                                                          self.factory.password))
        transition(self.factory, _AuthenticatingState)

    def subscribe(self, handler, destination, headers):
        self.factory._subscriptions.append((handler, destination, headers))
                                                        

class MQClientFactory(protocol.ReconnectingClientFactory):
    interface.implements(IMQClientFactory)

    protocol = MQClientProtocol

    def __init__(self, username='', password=''):
        self.username = username
        self.password = password
        self.session = None
        self.state = _ConnectingState(self)

        #
        # A map of destination queues to functions
        # to call
        self.subscriptionHandlers = {}
    
    def buildProtocol(self, addr):
        self.mqClient = self.protocol()
        self.mqClient.factory = self
        return self.mqClient


    def clientConnectionLost(self, connector, _reason):
        transition(self, _ConnectingState)
        connector.connect()
        
    def subscribe(self, handler, destination, headers):
        return self.state.subscribe(handler, destination, headers)

    def unsubscribe(self, destination):
        return self.state.unsubscribe(destination)
    
    def send(self, destination, headers, body):
        return self.state.send(destination, headers, body)
    
    def ack(self, messageId, headers):
        return self.state.ack(messageId, headers)

    def connectionMade(self):
        return self.state.connectionMade()
    
    def connectedReceived(self, msg):
        return self.state.connectedReceived(msg)
    
    def msgReceived(self, msg):
        return self.state.msgReceived(msg)
    
    def receiptReceived(self, msg):
        return self.state.receiptReceived(msg)
    
    def errorReceived(self, msg):
        return self.state.errorReceived(msg)


    def _removeSubscription(self, dest):
        self._subscriptions = [(handler, dst, hd) for handler, dst, hd in self._subscriptions if dst != destination]

    def _findSubscription(self, dest):
        for handler, dst, _hd in self._subscriptions:
            if dest == dst:
                return handler

        return None
    
def makeService(config):
    pass


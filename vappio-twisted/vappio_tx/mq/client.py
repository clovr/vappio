#
# Message Queue client that will use stomper for backend.
#
# To use, call makeService with a config so it knows who to connect
# and any username password login information.

from zope import interface

from twisted.application import internet

from twisted.internet import protocol
from twisted.internet import reactor

from twisted.python import log

from igs.utils import functional as func

from igs_tx.utils import global_state

from vappio_tx import stomper


def _iterFuncs(funcs):
    def _():
        for f in funcs:
            f()

    return _

def _updateOrCreateDict(d, updates):
    if d is None:
        d = {}

    return func.updateDict(d, updates)

class IMQClientFactory(interface.Interface):
    """
    Factory for MQ client protocol
    """

    def subscribe(handler, destination, headers, receipt):
        """
        Subscribe to a queue or topic and us the list of headers given on it

        A deferred is returned, if success None is passed, if failure, the failure

        handler is a function that is called upon the incoming of a message
        """

    def unsubscribe(destination, headers, receipt):
        """
        Unsubscribe form a destination
        """

    def send(destination, body, headers, receipt):
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
        
        (msg, remainingData) = stomper.unpack_frame(self.data)
        while msg is not None:
            self.data = remainingData
            self.ACTIONS[msg.cmd](self, msg)
            (msg, remainingData) = stomper.unpack_frame(self.data)


    def sendMessage(self, msg):
        self.transport.write(msg)


def transition(factory, newState):
    factory.state = newState(factory)

class _ConnectedState:
    def __init__(self, factory):
        self.factory = factory
        self.receipts = {}
        
        for subscription in self.factory._subscriptions:
            if subscription['receipt']:
                receiptId = 'subscribe-' + global_state.make_ref()
                self.receipts[receiptId] = subscription['receipt']
                headers = _updateOrCreateDict(subscription['headers'],
                                              {'receipt': receiptId})

                # We only want to call this the first time it happens, that way reconnects
                # are invisible to the user
                subscription['receipt'] = None
            else:
                headers = subscription['headers']
            self.factory.mqClient.sendMessage(stomper.subscribe(subscription['destination'],
                                                                ack=subscription['ack'],
                                                                headers=headers))

        for send in self.factory._sends:
            self.send(send['destination'],
                      send['body'],
                      send['headers'],
                      send['receipt'])

        # Once we have sent these remove them
        self.factory._sends = []

    def subscribe(self, handler, destination, headers=None, ack='client', receipt=None):
        # Setting receipt to none here because we know it will be fired when we send it now
        # unless something goes bad now..but what are the chances of that?
        self.factory._subscriptions.append({'handler': handler,
                                            'destination': destination,
                                            'headers': headers,
                                            'ack': ack,
                                            'receipt': None})
        if receipt:
            receiptId = receiptId = 'subscribe-' + global_state.make_ref()
            headers = _updateOrCreateDict(headers,
                                          {'receipt': receiptId})
            self.receipts[receiptId] = receipt            
        self.factory.mqClient.sendMessage(stomper.subscribe(destination, ack=ack, headers=headers))
        
    def unsubscribe(self, destination, headers=None, receipt=None):
        receiptId = 'unsubscribe-' + global_state.make_ref()
        if receipt:
            self.receipts[receiptId] = _iterFuncs([lambda : self.factory._removeSubscription(destination), receipt])
        else:
            self.receipts[receiptId] = lambda : self.factory._removeSubscription(destination)
        self.factory.mqClient.sendMessage(stomper.unsubscribe(destination, headers={'receipt': receiptId}))

    def send(self, destination, body, headers=None, receipt=None):
        if receipt:
            receiptId = receiptId = 'send-' + global_state.make_ref()
            headers = _updateOrCreateDict(headers,
                                          {'receipt': receiptId})
            self.receipts[receiptId] = receipt
        self.factory.mqClient.sendMessage(stomper.send(destination, body, headers))
        
    def ack(self, messageId, headers):
        self.factory.mqClient.sendMessage(stomper.ack(messageId, headers=headers))

    def msgReceived(self, msg):
        h = self.factory._findSubscription(msg.headers['destination'])
        if h:
            h(self.factory, msg)
        else:
            raise Exception('Received message on unknown subscription: ' + msg.headers['destination'])

    def receiptReceived(self, msg):
        receiptId = msg.headers['receipt-id']
        if receiptId not in self.receipts:
            raise Exception('Unknown receipt: ' + receiptId)
        else:
            self.receipts[receiptId]()
            del self.receipts[receiptId]

    def errorReceived(self, msg):
        raise Exception('Need to implement error: ' + str(msg))

    
class _AuthenticatingState:
    def __init__(self, factory):
        self.factory = factory

    def connectedReceived(self, msg):
        self.factory.session = msg.headers['session']

        transition(self.factory, _ConnectedState)

    def subscribe(self, handler, destination, headers=None, ack='client', receipt=None):
        self.factory._subscriptions.append({'handler': handler,
                                            'destination': destination,
                                            'headers': headers,
                                            'ack': ack,
                                            'receipt': receipt})

    def send(self, destination, body, headers=None, receipt=None):
        self.factory._sends.append({'destination': destination,
                                    'body': body,
                                    'headers': headers,
                                    'receipt': receipt})
        

class _ConnectingState:
    def __init__(self, factory):
        self.factory = factory
        
    def connectionMade(self):
        self.factory.mqClient.sendMessage(stomper.connect(self.factory.username,
                                                          self.factory.password))
        transition(self.factory, _AuthenticatingState)

    def subscribe(self, handler, destination, headers=None, ack='client', receipt=None):
        self.factory._subscriptions.append({'handler': handler,
                                            'destination': destination,
                                            'headers': headers,
                                            'ack': ack,
                                            'receipt': receipt})
                                                        
    def send(self, destination, body, headers=None, receipt=None):
        self.factory._sends.append({'destination': destination,
                                    'body': body,
                                    'headers': headers,
                                    'receipt': receipt})
        
class MQClientFactory(protocol.ReconnectingClientFactory):
    interface.implements(IMQClientFactory)

    protocol = MQClientProtocol

    def __init__(self, username='', password='', debug=False):
        self.username = username
        self.password = password
        self.debug = debug
        self.session = None
        self.state = _ConnectingState(self)

        #
        # A map of destination queues to functions
        # to call
        self._subscriptions = []

        self._sends = []
    
    def buildProtocol(self, addr):
        self.mqClient = self.protocol()
        self.mqClient.factory = self
        return self.mqClient


    def clientConnectionLost(self, connector, _reason):
        if self.debug:
            log.msg('MQClient - Connection lost, reconnecting')
        transition(self, _ConnectingState)
        connector.connect()
        
    def subscribe(self, handler, destination, headers=None, ack='client', receipt=None):
        return self.state.subscribe(handler, destination, headers, ack, receipt)

    def unsubscribe(self, destination, headers=None, receipt=None):
        return self.state.unsubscribe(destination, headers, receipt)
    
    def send(self, destination, body, headers=None, receipt=None):
        return self.state.send(destination, body, headers, receipt)
    
    def ack(self, messageId, headers=None):
        return self.state.ack(messageId, headers)

    def connectionMade(self):
        if self.debug:
            log.msg('MQClient - Connection made')
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
        self._subscriptions = [subscription
                               for subscription in self._subscriptions
                               if subscription['destination'] != dest]

    def _findSubscription(self, dest):
        for subscription in self._subscriptions:
            if dest == subscription['destination']:
                return subscription['handler']

        return None
    
def makeService(conf):
    mqFactory = MQClientFactory(conf('mq.username', default=''), conf('mq.password', default=''), debug=conf('mq.debug', default=False))
    mqService = internet.TCPClient(conf('mq.host'), int(conf('mq.port')), mqFactory)
    mqService.mqFactory = mqFactory
    return mqService

def connect(conf):
    mqFactory = MQClientFactory(conf('mq.username', default=''), conf('mq.password', default=''), debug=conf('mq.debug', default=False))
    reactor.connectTCP(conf('mq.host'), int(conf('mq.port')), mqFactory)
    return mqFactory

"""
This is a python client implementation of the STOMP protocol. 

It aims to be transport layer neutral. This module provides functions to 
create and parse STOMP messages in a programatic fashion.

The examples package contains two examples using twisted as the transport 
framework. Other frameworks can be used and I may add other examples as
time goes on.

The STOMP protocol specification maybe found here:

 * http://stomp.codehaus.org/Protocol

I've looked at the stomp client by Jason R. Briggs and have based the message
generation on how his client does it. The client can be found at the follow 
address however it isn't a dependancy.

 * http://www.briggs.net.nz/log/projects/stomppy

In testing this library I run against ActiveMQ project. The server runs
in java, however its fairly standalone and easy to set up. The projects
page is here:

 * http://activemq.apache.org/


(c) Oisin Mulvihill, 2007-07-26.
License: http://www.apache.org/licenses/LICENSE-2.0

"""
import re
import uuid
import types

import doc
import utils

from igs.utils import functional

# This is used as a return from message reponses functions.
# It is used more for readability more then anything or reason.
NO_RESPONSE_NEEDED = ''

# The version of the protocol we implement.
STOMP_VERSION = '1.0'

# Message terminator:
NULL = '\x00'

# STOMP Spec v1.0 valid commands:
VALID_COMMANDS = [
    'ABORT', 'ACK', 'BEGIN', 'COMMIT', 
    'CONNECT', 'CONNECTED', 'DISCONNECT', 'MESSAGE',
    'SEND', 'SUBSCRIBE', 'UNSUBSCRIBE',
    'RECEIPT', 'ERROR',    
]


def noneOrEmptyDict(d):
    if d is None:
        return {}
    else:
        return d

class FrameError(Exception):
    """Raise for problem with frame generation or parsing.
    """


class Frame(object):
    """This class is used to create or read STOMP message frames. 
    
    The method pack() is used to create a STOMP message ready
    for transmission.
    
    The method unpack() is used to read a STOMP message into 
    a frame instance. It uses the unpack_frame(...) function
    to do the intial parsing.

    The frame has three important member variables:
    
      * cmd
      * headers
      * body
     
    The 'cmd' is a property that represents the STOMP message 
    command. When you assign this a check is done to make sure
    its one of the VALID_COMMANDS. If not then FrameError will
    be raised.
    
    The 'headers' is a dictionary which the user can added to 
    if needed. There are no restrictions or checks imposed on 
    what values are inserted.
    
    The 'body' is just a member variable that the body text 
    is assigned to. 
    
    """    
    def __init__(self, cmd=None, headers=None, body=''):
        """Setup the internal state."""
        self._cmd = cmd.upper()
        self.body = body
        if headers is None:
            self.headers = {}
        else:
            self.headers = headers
    
    def getCmd(self):
        """Don't use _cmd directly!"""
        return self._cmd
        
    def setCmd(self, cmd):
        """Check the cmd is valid, FrameError will be raised if its not."""
        cmd = cmd.upper()
        if cmd not in VALID_COMMANDS:
            raise FrameError("The cmd '%s' is not valid! It must be one of '%s' (STOMP v%s)." % (
                cmd, VALID_COMMANDS, STOMP_VERSION)
            )
        else:
            self._cmd = cmd
    
    cmd = property(getCmd, setCmd)

    
    def pack(self):
        """Called to create a STOMP message from the internal values.
        """
        headers = ['%s:%s' % (h, str(v)) for h, v in self.headers.items()]
        headers = "\n".join(headers)        
        
        stomp_message = "%s\n%s\n\n%s%s\n" % (self._cmd, headers, self.body, NULL)

        return stomp_message

        
    def unpack(self, message):
        """Called to extract a STOMP message into this instance.
        
        message:
            This is a text string representing a valid 
            STOMP (v1.0) message.
        
        This method uses unpack_frame(...) to extract the 
        information, before it is assigned internally.

        retuned:
            The result of the unpack_frame(...) call.
        
        """
        if not message:
            raise FrameError("Unpack error! The given message isn't valid '%s'!" % message)
            
        msg = unpack_frame(message)
        
        self.cmd = msg['cmd']
        self.headers = msg['headers']
        
        # Assign directly as the message will have the null
        # character in the message already.
        self.body = msg['body']

        return msg


def unpack_frame(message):
    """
    Unpacks a frame from a STOMP message.  If a content-length is in the
    headers then it ensures the body is that many elements long

    This returns a tuple (unpacked_frame, remaining bytes)
    """

    def _splitStrip(s):
        k, v = s.split(':', 1)
        return (k.strip(), v.strip())


    try:
        msg, rest = message.split('\000', 1)
        cmd_headers, body = msg.split('\n\n', 1)
        if len(cmd_headers.split('\n', 1)) == 2:
            cmd, headers = cmd_headers.lstrip().split('\n', 1)
            headers = dict([_splitStrip(s) for s in headers.split('\n')])
        else:
            cmd = cmd_headers
            headers = {}


        if 'content-length' in headers:
            nlen = int(headers['content-length']) - len(body)
            if nlen > 0 and len(rest) >= nlen:
                body += '\000' + rest[:nlen]
                rest = rest[nlen:]

        return (Frame(cmd=cmd,
                      headers=headers,
                      body=body),
                rest)
    except ValueError, err:
        if 'unpack' in str(err):
            return (None, message)
        else:
            raise

    
def pack_frame(msg):
    return Frame(cmd=msg['cmd'], headers=msg['headers'], body=msg['body']).pack()

def abort(transactionid, headers=None):
    """STOMP abort transaction command.

    Rollback whatever actions in this transaction.
        
    transactionid:
        This is the id that all actions in this transaction.
    
    """

    return Frame(cmd='ABORT',
                 headers=functional.updateDict(noneOrEmptyDict(headers),
                                               {'transaction': transactionid})).pack()


def ack(messageid, transactionid=None, headers=None):
    """STOMP acknowledge command.
    
    Acknowledge receipt of a specific message from the server.

    messageid:
        This is the id of the message we are acknowledging,
        what else could it be? ;)
    
    transactionid:
        This is the id that all actions in this transaction 
        will have. If this is not given then a random UUID
        will be generated for this.
    
    """
    headers = functional.updateDict(noneOrEmptyDict(headers),
                                    {'message-id': messageid})
    header = 'message-id: %s' % messageid

    if transactionid:
        headers = functional.updateDict(headers,
                                        {'transaction': messageid})

    return Frame(cmd='ACK', headers=headers).pack()


    
def begin(transactionid=None):
    """STOMP begin command.

    Start a transaction...
    
    transactionid:
        This is the id that all actions in this transaction 
        will have. If this is not given then a random UUID
        will be generated for this.
    
    """
    if not transactionid:
        # Generate a random UUID:
        transactionid = uuid.uuid4()

    return Frame(cmd='BEGIN', headers={'transaction': transactionid}).pack()
    
def commit(transactionid):
    """STOMP commit command.

    Do whatever is required to make the series of actions
    permenant for this transactionid.
        
    transactionid:
        This is the id that all actions in this transaction.
    
    """
    return Frame(cmd='COMMIT', headers={'transaction': transactionid}).pack()    


def connect(username, password):
    """STOMP connect command.
    
    username, password:
        These are the needed auth details to connect to the 
        message server.
    
    After sending this we will receive a CONNECTED
    message which will contain our session id.
    
    """
    headers = {}
    if username:
        headers['login'] = username

    if password:
        headers['passcode'] = password
        
    return Frame(cmd='CONNECT', headers=headers).pack()


def disconnect():
    """STOMP disconnect command.
    
    Tell the server we finished and we'll be closing the
    socket soon.
    
    """
    return Frame(cmd='DISCONNECT').pack()

    
def send(dest, body, headers=None, transactionid=None):
    """STOMP send command.
    
    dest:
        This is the channel we wish to subscribe to
    
    msg:
        This is the message body to be sent.
        
    transactionid:
        This is an optional field and is not needed
        by default.
    
    """
    if transactionid:
        headers = functional.updateDict(noneOrEmptyDict(headers), {'transaction': transactionid})

    headers = functional.updateDict(noneOrEmptyDict(headers),
                                    {'content-length': len(body),
                                     'destination': dest})

    return Frame(cmd='SEND', headers=headers, body=body).pack()
    
def subscribe(dest, ack='auto', headers=None):
    """STOMP subscribe command.
    
    dest:
        This is the channel we wish to subscribe to
    
    ack: 'auto' | 'client'
        If the ack is set to client, then messages received will
        have to have an acknowledge as a reply. Otherwise the server
        will assume delivery failure.
    
    """
    return Frame(cmd='SUBSCRIBE',
                 headers=functional.updateDict(noneOrEmptyDict(headers), {'ack': ack,
                                                                          'destination': dest})).pack()

def unsubscribe(dest, receipt=None):
    """STOMP unsubscribe command.
    
    dest:
        This is the channel we wish to subscribe to
    
    Tell the server we no longer wish to receive any
    further messages for the given subscription.
    
    """
    if receipt:
        headers = {'receipt': receipt,
                   'destination': dest}
    else:
        headers = {'destination': dest}
    return Frame(cmd='UNSUBSCRIBE',
                 headers=headers).pack()

class Engine(object):
    """This is a simple state machine to return a response to received 
    message if needed.
    
    """
    def __init__(self, testing=False):
        self.testing = testing
        
        #self.log = logging.getLogger("stomper.Engine")
        
        self.sessionId = ''
        
        # Entry Format:
        #
        #    COMMAND : Handler_Function 
        #
        self.states = {
            'CONNECTED' : self.connected,
            'MESSAGE' : self.ack,
            'ERROR' : self.error,
            'RECEIPT' : self.receipt,
        }
        
                
    def react(self, msg):
        """Called to provide a response to a message if needed.
        
        msg:
            This is a dictionary as returned by unpack_frame(...)
            or it can be a straight STOMP message. This function
            will attempt to determine which an deal with it.

        returned:
            A message to return or an empty string.
            
        """
        returned = ""

        # If its not a string assume its a dict. 
        mtype = type(msg)
        if mtype in types.StringTypes:
            msg = unpack_frame(msg)        
        elif mtype == types.DictType:
            pass
        else:
            raise FrameError("Unknown message type '%s', I don't know what to do with this!" % mtype)
        
        if self.states.has_key(msg['cmd']):
            returned = self.states[msg['cmd']](msg)
            
        return returned
        
        
    def connected(self, msg):
        """No reponse is needed to a connected frame. 
        
        This method stores the session id as a the 
        member sessionId for later use.
        
        returned:
            NO_RESPONSE_NEEDED
            
        """
        self.sessionId = msg['headers']['session']
        
        return NO_RESPONSE_NEEDED


    def ack(self, msg):
        """Called when a MESSAGE has been received.
        
        Override this method to handle received messages.
        
        This function will generate an acknowlege message 
        for the given message and transaction (if present).
        
        """
        message_id = msg['headers']['message-id']

        transaction_id = None
        if msg['headers'].has_key('transaction-id'):
            transaction_id = msg['headers']['transaction-id']
        
        
        return ack(message_id, transaction_id)


    def error(self, msg):
        """Called to handle an error message received from the server.
        
        This method just logs the error message
        
        returned:
            NO_RESPONSE_NEEDED
        
        """
        body = msg['body'].replace(NULL, '')
        
        brief_msg = ""
        if msg['headers'].has_key('message'):
            brief_msg = msg['headers']['message']
        
        #self.log.error("Received server error - message%s\n\n%s" % (brief_msg, body))
        
        returned = NO_RESPONSE_NEEDED
        if self.testing:
            returned = 'error'
            
        return returned


    def receipt(self, msg):
        """Called to handle a receipt message received from the server.
        
        This method just logs the receipt message
        
        returned:
            NO_RESPONSE_NEEDED
        
        """
        body = msg['body'].replace(NULL, '')
        
        brief_msg = ""
        if msg['headers'].has_key('receipt-id'):
            brief_msg = msg['headers']['receipt-id']
        
        #self.log.info("Received server receipt message - receipt-id:%s\n\n%s" % (brief_msg, body))
        
        returned = NO_RESPONSE_NEEDED
        if self.testing:
            returned = 'receipt'
            
        return returned


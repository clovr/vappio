#
# Message Queue client that will use stomper for backend.
#
# To use, call makeService with a config so it knows who to connect
# and any username password login information.

from zope import interface

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




def makeService(config):
    pass


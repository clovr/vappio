from zope import interface


class IMesssageQueueService(interface.Interface):

    def getMessage():
        """Gets a message from the queue"""

    def putMessage(msg):
        """Puts a message on the queue"""

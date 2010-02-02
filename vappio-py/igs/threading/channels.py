##
# Channels provide a means of communicatin between threads
from Queue import Queue

class Channel:
    """
    A channel is a unidirectional form of communication between threads.  All channel operations are asynchronous/nonblocking
    unless otherwise specified.
    
    A channel allows for the following actions:

    send - Send an object over the channel
    receive - Receive an object from a channel
    NOTE - One thread should only be send'ing and the other thread only receive'ing.  Channels unidirectional

    sendWithChannel - Send an object and create a receive channel, and return it.  The object will be sent as a tuple (object, Channel).
                      This is useful if you want to send a task to perform and get a result back, the channel is almost like a 'future'
                      but not quite.

    """
    
    def __init__(self):
        self.queue = Queue()


    def send(self, obj):
        """Send 'obj' through the channel"""

        self.queue.put_nowait(obj)


    def sendWithChannel(self, obj):
        """Send 'obj' as well as a new channel through this channel and return the new channel"""
        ch = Channel()
        self.send((obj, ch))
        return ch
        
    def receive(self, block=False, timeout=None):
        """
        Receive an object from the channel.  Where block=True, timeout=None it will block indefinitely
        """

        item = self.queue.get(block, timeout)
        self.queue.task_done()
        return item

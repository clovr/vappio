##
# Various exceptions/errors can be defined here
import traceback
from StringIO import StringIO

class Error(Exception):
    pass

class TryError(Error):
    """
    Used when you want to try something but it fails but you want to return
    a partial result.  

    .result contains this result
    .msg contains whatever message the caller put in there
    """
    def __init__(self, msg, result):
        self.msg = msg
        self.result = result

    def __str__(self):
        return str(self.msg) + '\n' + str(self.result)

class RemoteError(Error):
    def __init__(self, name, msg, stacktrace):
        Error.__init__(self)
        self.name = name
        self.msg = msg
        self.stacktrace = stacktrace

    def __str__(self):
        return 'Name: %s\nMsg: %s\nStacktrace: %s' % (self.name,
                                                      self.msg,
                                                      self.stacktrace)

def getStacktrace():
    stream = StringIO()
    traceback.print_exc(file=stream)
    return stream.getvalue()

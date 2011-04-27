import StringIO
import traceback

def stackTraceToString(failure):
    """
    Converts a failure to a string containing the stack trace
    """
    return ''.join(traceback.format_tb(failure.getTracebackObject()))


def getStacktrace():
    stream = StringIO.StringIO()
    traceback.print_exc(file=stream)
    return stream.getvalue()


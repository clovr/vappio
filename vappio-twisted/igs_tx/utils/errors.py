import traceback

def stackTraceToString(failure):
    """
    Converts a failure to a string containing the stack trace
    """
    return '\n'.join(traceback.format_tb(failure.getTracebackObject()))


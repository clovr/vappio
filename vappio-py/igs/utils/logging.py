##
# Various tools for logging
import sys
import time

OUTSTREAM = sys.stdout
ERRSTREAM = sys.stderr

##
# Debug mode on?
DEBUG = False

def logPrint(msg, stream=None):
    if stream is None:
        stream = OUTSTREAM
    stream.write('LOG: %s - %s\n' % (timestamp(), msg))


def errorPrint(msg, stream=None):
    if stream is None:
        stream = ERRSTREAM

    stream.write('ERROR: %s - %s\n' % (timestamp(), msg))

def debugPrint(fmsg, stream=None):
    """In this case msg is a function, so the work is only done if debugging is one"""
    if DEBUG:
        if stream is None:
            stream = ERRSTREAM

        stream.write('DEBUG: %s - %s\n' % (timestamp(), fmsg()))


def timestamp():
    return time.strftime('%Y/%m/%d %H:%M:%S')


##
# These version strip off the right white spaces so they can be used in printing output from a program
errorPrintS = lambda l *args **kwargs : errorPrint(l.rstrip(), *args, **kwargs)

logPrintS = lambda l *args **kwargs : logPrint(l.rstrip(), *args, **kwargs)

debugPrintS = lambda f *args **kwargs : debugPrint(lambda : f().rstrip(), *args, **kwargs)

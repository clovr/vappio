##
# This is a script for doing init.d-like things in Python.
# You simply give it a map of (node-type, function) and it executes
# them with a config file

from igs.utils.errors import TryError
from igs.utils.logging import errorPrint

from vappio.instance.config import RELEASE_CUT

def runInit(conf, funcs):
    """
    The config must be created through vappio.instance.config.configFrom(Stream|Map)

    Funcs should have keys for:
    pre - Any work that needs to be done before each node type is executed
    Keys for all nodes types
    post - Any work that needs to be done after each node type is executed
    """

    ##
    # If we are just cutting a release, don't do any of this
    if RELEASE_CUT not in conf('NODE_TYPE'):
        ##
        # Perform any pre work first
        funcs['pre'](conf)

        ##
        # Run it for each node type
        for n in conf('NODE_TYPE'):
            funcs[n](conf)

        ##
        # Perform post work
        funcs['post'](conf)

        


def executePolicyDir(func, d, prefix=None):
    """
    Execute all .py files in a directory, in alphabetical order, calling func on the module

    This throws a TryError if any of the modules fail.  The result is a list of tuples consisting
    of the module name and str rep of the exception
    """
    ##
    # a bit cheap but we want to temporarily make this direcotry in our path if it isn't already
    # so safe out sys.path, add d to it, and put it back when done
    oldpath = sys.path
    sys.path = [d] + sys.path
    path = d
    if prefix:
        path = os.path.join(path, prefix)
    files = [f[:-3]
             for f in os.listdir(path)
             if f.endswith('.py') and f != '__init__.py']
    files.sort()
    errorRes = []
    try:
        for f in files:
            if prefix:
                f = prefix + '.' + f
            try:
                m = namedModule(f)
                func(m)
            except Exception, err:
                errorRes.append((f, str(err)))
    finally:
        sys.path = oldpath

    if errorRes:
        raise TryError('Failed to execute all modules', errorRes)
        

def executePolicyDirWEx(func, d, prefix=None):
    """
    This runs executePolicyDir but catches teh TryError and prints out
    diagnostic information. and returns safely
    """
    try:
        executePolicyDir(func, d, prefix)
    except TryError, err:
        errorPrint('Failed to execute some modules')
        for m, e in err.result:
            errorPrint('Module: %15s Error: %s' % (m, e))

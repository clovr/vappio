##
# This is a script for doing init.d-like things in Python.
# You simply give it a map of (node-type, function) and it executes
# them with a config file

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

        

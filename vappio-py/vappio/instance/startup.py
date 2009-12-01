##
# This is a series of functions for controlling the startup of an instance
import os

from igs.utils.commands import runSystemEx

from vappio.instance.config import DEV_NODE, MASTER_NODE, EXEC_NODE, configFromStream


##
# I'm using lambdas here just because I want to define the functions lower in the file
# and they need to exist before I can reference them, unless I wrap them in a lambda
NODE_TYPE_MAP = {
    DEV_NODE: lambda c : startUpDevNode(c),
    MASTER_NODE: lambda c : startUpMasterNode(c),
    EXEC_NODE: lambda c : startUpExecNode(c)
    }

def startUp(conf):
    """
    Runs all necessary steps to properly start a machine up based on the config given

    The config must be created through vappio.instance.config.configFrom(Stream|Map)
    """
    for n in conf('NODE_TYPE'):
        NODE_TYPE_MAP[n](conf)

    ##
    # For those things that need to be started everywhere
    startUpAllNodes(conf)

def startUpFromConfigFile(fname):
    """Run startup from a config file"""
    return startUp(configFromStream(open(fname)))

def startUpDevNode(conf):
    """
    Steps in starting a dev node:

    1 - Remove /usr/local/stow (this should be a config option eventually)
    2 - Check out /usr/local/stow
    3 - Check out /opt/packages

    Any SVN work is done on trunk (need to add config to specify a branch)
    """
    runSystemEx("""rm -rf /usr/local/stow""")
    runSystemEx("""svn co https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/stow /usr/local/stow""")

    runSystemEx("""rm -rf /opt/packages""")
    runSystemEx("""svn co https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/packages /opt/packages""")

def startUpMasterNode(conf):
    """
    Not sure what, if anything, needs to be done here
    """
    pass
    

def startUpExecNode(conf):
    """
    Just need to run the vappio-script for starting the exec node
    This should eventually replace that script
    """
    runSystemEx("""/opt/vappio-scripts/start_exec.sh %s""" % (conf('MASTER_IP'),))


def startUpAllNodes(conf):
    """
    Things that need to be done for all nodes:

    1 - List through all .py files in /opt/config_policies and run them (eventually this directory should probably
        be split up by node type)
    """
    for f in os.listdir('/opt/config_policies'):
        if f.endswith('.py'):
            runSystemEx('python ' + os.path.join('/opt/config_policies', f))
            

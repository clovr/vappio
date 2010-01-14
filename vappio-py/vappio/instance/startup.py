##
# This is a series of functions for controlling the startup of an instance
import os

from igs.utils.commands import runSystemEx
from igs.utils.config import configFromEnv


from vappio.instance.config import DEV_NODE, MASTER_NODE, EXEC_NODE, RELEASE_CUT, configFromStream


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

    ##
    # If we are just cutting a release, don't do any of this
    if RELEASE_CUT not in conf('NODE_TYPE'):
        ##
        # For those things that need to be started everywhere
        startUpAllNodes(conf)
    
        for n in conf('NODE_TYPE'):
            NODE_TYPE_MAP[n](conf)



def startUpFromConfigFile(fname):
    """Run startup from a config file"""
    return startUp(configFromStream(open(fname)), configFromEnv())

def startUpDevNode(conf):
    """
    Steps in starting a dev node:

    1 - Remove /usr/local/stow (this should be a config option eventually)
    2 - Check out /usr/local/stow
    3 - Check out /opt/packages

    Any SVN work is done on trunk (need to add config to specify a branch)
    """
    executePolicyDir('/opt/config_policies/DEV')
    runSystemEx("""rm -rf /usr/local/stow""")
    runSystemEx("""svn co https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/stow /usr/local/stow""")

    runSystemEx("""rm -rf /opt/packages""")
    runSystemEx("""svn co https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/packages /opt/packages""")

    runSystemEx("""rm -rf /opt/clovr_pipelines""")
    runSystemEx("""svn co https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/clovr_pipelines /opt/clovr_pipelines""")

    runSystemEx("""rm -rf /opt/opt-packages""")
    runSystemEx("""svn co https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/opt-packages /opt/opt-packages""")

def startUpMasterNode(conf):
    """
    1 - Setup hadoop
    """
    executePolicyDir('/opt/config_policies/MASTER')
    

def startUpExecNode(conf):
    """
    Just need to run the vappio-script for starting the exec node
    This should eventually replace that script
    """
    executePolicyDir('/opt/config_policies/EXEC')
    ##
    # Don't need this now
    #runSystemEx("""/opt/vappio-scripts/start_exec.sh %s""" % (conf('MASTER_IP'),))


def startUpAllNodes(conf):
    """
    Things that need to be done for all nodes:

    1 - List through all .py files in /opt/config_policies and run them (eventually this directory should probably
        be split up by node type)
    """
    executePolicyDir('/opt/config_policies')
            

def executePolicyDir(d):
    """Execute all .py files in a directory, in alphabetical order"""
    files = [f for f in os.listdir(d) if f.endswith('.py')]
    files.sort()
    for f in files:
        runSystemEx('python ' + os.path.join(d, f))
        

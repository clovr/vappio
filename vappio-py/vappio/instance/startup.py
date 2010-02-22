##
# This is a series of functions for controlling the startup of an instance
import sys
import os

from twisted.python.reflect import namedModule

from igs.utils.errors import TryError
from igs.utils.commands import runSystemEx
from igs.utils.functional import const

from igs.config_manage.policy import installPkg, installOptPkg

from vappio.instance.init_instance import runInit, executePolicyDirWEx
from vappio.instance.config import DEV_NODE, MASTER_NODE, EXEC_NODE, RELEASE_CUT, configFromStream




##
# I'm using lambdas here just because I want to define the functions lower in the file
# and they need to exist before I can reference them, unless I wrap them in a lambda
NODE_TYPE_MAP = {
    'pre': lambda c : startUpAllNodes(c),
    DEV_NODE: lambda c : startUpDevNode(c),
    MASTER_NODE: lambda c : startUpMasterNode(c),
    EXEC_NODE: lambda c : startUpExecNode(c),
    'post': const(None)
    }

def startUp(conf):
    runInit(conf, NODE_TYPE_MAP)


def startUpFromConfigFile(fname):
    """Run startup from a config file"""
    return startUp(configFromStream(open(fname)))


def startPolicy(m):
    """
    Calls startup on the policy
    """
    m.startup()

def startUpDevNode(conf):
    """
    Steps in starting a dev node:

    1 - Remove /usr/local/stow (this should be a config option eventually)
    2 - Check out /usr/local/stow
    3 - Check out /opt/packages

    Any SVN work is done on trunk (need to add config to specify a branch)
    """
    executePolicyDirWEx('/opt/config_policies', 'DEV')
    runSystemEx("""updateAllDirs.py --co""")

def startUpMasterNode(conf):
    executePolicyDirWEx(startPolicy, '/opt/config_policies', 'MASTER')
    
    ##
    # Run anything for internal record keeping in a database
    ##
    # I don't think I need this yet
    #setupDatabase(conf)

def startUpExecNode(conf):
    """
    Just need to run the vappio-script for starting the exec node
    This should eventually replace that script
    """
    executePolicyDirWEx(startPolicy, '/opt/config_policies', 'EXEC')
    ##
    # Don't need this now
    #runSystemEx("""/opt/vappio-scripts/start_exec.sh %s""" % (conf('MASTER_IP'),))


def startUpAllNodes(conf):
    """
    Things that need to be done for all nodes:

    1 - Go through /usr/local/stow and /opt/opt-packages installing all packages
    2 - List through all .py files in /opt/config_policies and run them (eventually this directory should probably
        be split up by node type)
    """
    installAllStow()
    installAllOptPackages()            
    executePolicyDirWEx(startPolicy, '/opt/config_policies')



def installAllStow():
    for p in os.listdir('/usr/local/stow'):
        installPkg(p)
        

def installAllOptPackages():
    for p in os.listdir('/opt/opt-packages'):
        installOptPkg(p)
        

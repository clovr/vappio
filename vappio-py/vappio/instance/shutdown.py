##
# How we want to bring down the node
import sys
import os

from twisted.python.reflect import namedModule

from igs.utils.errors import TryError
from igs.utils.functional import const

from igs.config_manage.policy import uninstallPkg, uninstallOptPkg

from vappio.instance.init_instance import runInit, executePolicyDirWEx
from vappio.instance.config import DEV_NODE, MASTER_NODE, EXEC_NODE, RELEASE_CUT, configFromStream

##
# I'm using lambdas here just because I want to define the functions lower in the file
# and they need to exist before I can reference them, unless I wrap them in a lambda
NODE_TYPE_MAP = {
    'pre': const(None),
    DEV_NODE: lambda c : shutdownDevNode(c),
    MASTER_NODE: lambda c : shutdownMasterNode(c),
    EXEC_NODE: lambda c : shutdownExecNode(c),
    'post': lambda c : shutdownAllNodes(c)
    }


def shutdown(conf):
    """
    Does everything necessary for shutdown an instance and cleaning everything up
    """
    runInit(conf, NODE_TYPE_MAP)


def shutdownFromConfigFile(fname):
    """Run startup from a config file"""
    return shutdown(configFromStream(open(fname)))


def shutdownPolicy(m):
    """
    Calls startup on the policy
    """
    m.shutdown()


def shutdownAllNodes(conf):
    """
    Goes through all of stow and
    """
    executePolicyDirWEx(shutdownPolicy, '/opt/config_policies')
    uninstallAllStow()
    uninstallAllOptPackages()


def shutdownDevNode(conf):
    executePolicyDirWEx(shutdownPolicy, '/opt/config_policies', 'DEV')


def shutdownMasterNode(conf):
    executePolicyDirWEx(shutdownPolicy, '/opt/config_policies', 'MASTER')


def shutdownExecNode(conf):
    executePolicyDirWEx(shutdownPolicy, '/opt/config_policies', 'EXEC')

        
def uninstallAllStow():
    for p in os.listdir('/usr/local/stow'):
        uninstallPkg(p)

def uninstallAllOptPackages():
    for p in os.listdir('/opt/opt-packages'):
        uninstallOptPkg(p)

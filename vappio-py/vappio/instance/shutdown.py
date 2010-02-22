##
# How we want to bring down the node
import sys
import os

from twisted.python.reflect import namedModule

from igs.utils.functional import const

from igs.config_manage.policy import uninstallPkg, uninstallOptPkg

from vappio.instance.init_instance import runInit
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

    
def shutdownAllNodes(conf):
    """
    Goes through all of stow and
    """
    executePolicyDir('/opt/config_policies')
    uninstallAllStow()
    uninstallAllOptPackages()


def shutdownDevNode(conf):
    executePolicyDir('/opt/config_policies/DEV')


def shutdownMasterNode(conf):
    executePolicyDir('/opt/config_policies/MASTER')


def shutdownExecNode(conf):
    executePolicyDir('/opt/config_policies/EXEC')




##
# TODO: Refactor this so startup and shutdown us eteh same one, only diff is
# in calling m.shutdown
def executePolicyDir(d):
    """Execute all .py files in a directory, in alphabetical order"""
    ##
    # a bit cheap but we want to temporarily make this direcotry in our path if it isn't already
    # so safe out sys.path, add d to it, and put it back when done
    oldpath = sys.path
    sys.path = [d] + sys.path
    files = [f[:-3] for f in os.listdir(d) if f.endswith('.py') and f != '__init__.py']
    files.sort()
    try:
        for f in files:
            m = namedModule(f)
            m.shutdown()
    finally:
        sys.path = oldpath
        


def uninstallAllStow():
    for p in os.listdir('/usr/local/stow'):
        uninstallPkg(p)

def uninstallAllOptPackages():
    for p in os.listdir('/opt/opt-packages'):
        uninstallOptPkg(p)

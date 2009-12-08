##
# Functions for creating a config + useful constants
from igs.utils import config


DEV_NODE = 'DEV'
MASTER_NODE = 'MASTER'
EXEC_NODE = 'EXEC'

def createDataFile(conf, mode, masterHost):
    open('/tmp/machine.conf', 'w').write(open(conf('instance.conf')).read())
    open('/tmp/machine.conf', 'a').write('\n'.join(
        ['[]',
         'MASTER_IP=' + masterHost,
         'NODE_TYPE=' + ','.join(mode)]) + '\n')

    return '/tmp/machine.conf'


def configFromStream(stream):
    return fixVariables(config.configFromStream(stream))


def fixVariables(conf):
    """
    Takes a conf and returns a new one that has the proper types in places
    """
    return config.configFromMap({'NODE_TYPE': conf('NODE_TYPE').split(',')}, conf)

##
# Functions for creating a config + useful constants
import os


from igs.utils import config
from igs.utils.commands import runSingleProgram, ProgramRunError

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


def createMasterDataFile(conf):
    """
    Creates a master data file as the perl start_cluster works
    """
    template = open(conf('cluster.master_user_data_tmpl')).read()
    clusterPrivateKey = open(conf('cluster.cluster_private_key')).read()
    
    outf = []
    exitCode = runSingleProgram('ssh-keygen -y -f ' + conf('cluster.cluster_private_key'),
                                outf.append,
                                None,
                                log=True)
    if exitCode != 0:
        raise ProgramRunError('ssh-keygen -y -f ' + conf('cluster.cluster_private_key'), exitCode)

    clusterPublicKey = ''.join(outf)

    template = template.replace('<TMPL_VAR NAME=CLUSTER_PRIVATE_KEY>', clusterPrivateKey)
    template = template.replace('<TMPL_VAR NAME=CLUSTER_PUBLIC_KEY>', clusterPublicKey)

    outf = os.path.join(conf('general.secure_tmp'), 'master_user_data.sh')
    open(outf, 'w').write(template)

    return outf


def createExecDataFile(conf):
    """
    Creates a exec data file as the perl start_cluster works

    This is very similar to createMasterDataFile, should be refactored a bit
    """
    template = open(conf('cluster.exec_user_data_tmpl')).read()
    clusterPrivateKey = open(conf('cluster.cluster_private_key')).read()
    
    outf = []
    exitCode = runSingleProgram('ssh-keygen -y -f ' + conf('cluster.cluster_private_key'),
                                outf.append,
                                None,
                                log=True)
    if exitCode != 0:
        raise ProgramRunError('ssh-keygen -y -f ' + conf('cluster.cluster_private_key'), exitCode)

    clusterPublicKey = ''.join(outf)

    template = template.replace('<TMPL_VAR NAME=CLUSTER_PRIVATE_KEY>', clusterPrivateKey)
    template = template.replace('<TMPL_VAR NAME=CLUSTER_PUBLIC_KEY>', clusterPublicKey)

    outf = os.path.join(conf('general.secure_tmp'), 'exec_user_data.sh')
    open(outf, 'w').write(template)

    return outf


##
# Functions for creating a config + useful constants
import os


from igs.utils import config, logging
from igs.utils.commands import runSingleProgram, ProgramRunError


DEV_NODE = 'DEV'
MASTER_NODE = 'MASTER'
EXEC_NODE = 'EXEC'
RELEASE_CUT = 'RELEASE_CUT'

def createDataFile(conf, mode, masterHost, outFile='/tmp/machine.conf'):
    ##
    # We want everything from the clovr config in here for now
    fout = open(outFile, 'w')
    fout.write(open(conf('general.conf')).read())
    fout.write(open(conf('instance.config_file')).read())
    fout.write('\n'.join(
            ['[]',
             'MASTER_IP=' + masterHost,
             'NODE_TYPE=' + ','.join(mode),
             ##
             # The cluster needs to know this
             'general.ctype=' + conf('general.ctype', default='UNKNOWN')]) + '\n')

    return outFile


def configFromStream(stream):
    return fixVariables(config.configFromStream(stream, config.configFromEnv()))


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
                                log=logging.DEBUG)
    if exitCode != 0:
        raise ProgramRunError('ssh-keygen -y -f ' + conf('cluster.cluster_private_key'), exitCode)

    clusterPublicKey = ''.join(outf)

    template = template.replace('<TMPL_VAR NAME=CLUSTER_PRIVATE_KEY>', clusterPrivateKey)
    template = template.replace('<TMPL_VAR NAME=CLUSTER_PUBLIC_KEY>', clusterPublicKey)

    outf = os.path.join(conf('general.secure_tmp'), 'master_user_data.sh')
    open(outf, 'w').write(template)

    return outf


def createExecDataFile(conf, master):
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

    if conf('general.ctype') == 'ec2':
        template = template.replace('<TMPL_VAR NAME=MASTER_PRIVATE_DNS>', master.privateDNS)
    else:
        template = template.replace('<TMPL_VAR NAME=MASTER_PRIVATE_DNS>', master.publicDNS)
    
    clusterPublicKey = ''.join(outf)

    template = template.replace('<TMPL_VAR NAME=CLUSTER_PRIVATE_KEY>', clusterPrivateKey)
    template = template.replace('<TMPL_VAR NAME=CLUSTER_PUBLIC_KEY>', clusterPublicKey)

    outf = os.path.join(conf('general.secure_tmp'), 'exec_user_data.sh')
    open(outf, 'w').write(template)

    return outf


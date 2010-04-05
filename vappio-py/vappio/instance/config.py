##
# Functions for creating a config + useful constants
import os
import time

from igs.utils import config, logging
from igs.utils.commands import runSingleProgramEx


DEV_NODE = 'DEV'
MASTER_NODE = 'MASTER'
EXEC_NODE = 'EXEC'
RELEASE_CUT = 'RELEASE_CUT'

def createDataFile(conf, mode, outFile='/tmp/machine.conf'):
    ##
    # We want everything from the clovr config in here for now
    fout = open(outFile, 'w')
    fout.write(open(conf('general.conf')).read())
    fout.write(open(conf('instance.config_file')).read())
    fout.write('\n'.join([
                '[]',
                'NODE_TYPE=' + ','.join(mode),
                'general.ctype=' + conf('general.ctype', default='UNKNOWN')
                ]) + '\n')
            
    #fout.write('\n'.join(
    #        ['[]',
    #         'MASTER_IP=' + masterHost,
    #         'NODE_TYPE=' + ','.join(mode),
    #         ##
    #         # The cluster needs to know this
    #         'general.ctype=' + conf('general.ctype', default='UNKNOWN')]) + '\n')

    fout.close()
    
    return outFile


def configFromStream(stream):
    return fixVariables(config.configFromStream(stream, config.configFromEnv()))


def fixVariables(conf):
    """
    Takes a conf and returns a new one that has the proper types in places
    """
    return config.configFromMap({'NODE_TYPE': conf('NODE_TYPE').split(',')}, conf)


def createMasterDataFile(conf, machineConf, certFile, pkFile):
    """
    Creates a master data file as the perl start_cluster works
    """
    template = open(conf('cluster.master_user_data_tmpl')).read()
    clusterPrivateKey = open(conf('cluster.cluster_private_key')).read()
    
    outf = []
    runSingleProgramEx('ssh-keygen -y -f ' + conf('cluster.cluster_private_key'),
                       outf.append,
                       None,
                       log=logging.DEBUG)

    clusterPublicKey = ''.join(outf)

    template = template.replace('<TMPL_VAR NAME=CLUSTER_PRIVATE_KEY>', clusterPrivateKey)
    template = template.replace('<TMPL_VAR NAME=CLUSTER_PUBLIC_KEY>', clusterPublicKey)
    template = template.replace('<TMPL_VAR NAME=MACHINE_CONF>', open(machineConf).read().replace('${', '\\${'))
    template = template.replace('<TMPL_VAR NAME=CERT_FILE>', open(certFile).read())
    template = template.replace('<TMPL_VAR NAME=PK_FILE>', open(pkFile).read())

    outf = os.path.join(conf('general.secure_tmp'), 'master_user_data.sh')
    open(outf, 'w').write(template)

    return outf


def createExecDataFile(conf, master, masterMachineConf):
    """
    Creates a exec data file as the perl start_cluster works

    This is very similar to createMasterDataFile, should be refactored a bit
    """
    outName = os.path.join('/tmp', str(time.time()))

    ##
    # Going to load the master machine.conf and modify node type
    masterConf = config.configFromStream(open(masterMachineConf), lazy=True)
    masterConf = config.configFromMap({'NODE_TYPE': EXEC_NODE}, masterConf, lazy=True)

    fout = open(outName, 'w')
    fout.write('\n'.join([k + '=' + str(v) for k, v in config.configToDict(masterConf).iteritems()]))
    fout.close()

    
    template = open(conf('cluster.exec_user_data_tmpl')).read()
    clusterPrivateKey = open(conf('cluster.cluster_private_key')).read()
    
    outf = []
    runSingleProgramEx('ssh-keygen -y -f ' + conf('cluster.cluster_private_key'),
                       outf.append,
                       None,
                       log=True)

    if conf('general.ctype') == 'ec2':
        template = template.replace('<TMPL_VAR NAME=MASTER_PRIVATE_DNS>', master.privateDNS)
    else:
        template = template.replace('<TMPL_VAR NAME=MASTER_PRIVATE_DNS>', master.publicDNS)
    
    clusterPublicKey = ''.join(outf)

    template = template.replace('<TMPL_VAR NAME=CLUSTER_PRIVATE_KEY>', clusterPrivateKey)
    template = template.replace('<TMPL_VAR NAME=CLUSTER_PUBLIC_KEY>', clusterPublicKey)
    template = template.replace('<TMPL_VAR NAME=MACHINE_CONF>', open(outName).read().replace('${', '\\${'))

    os.remove(outName)
    
    outf = os.path.join(conf('general.secure_tmp'), 'exec_user_data.sh')
    open(outf, 'w').write(template)
    

    return outf


##
# This just hands the work off to a remote machine
import optparse

from igs.utils.cli import buildConfig, MissingOptionError
from igs.utils.config import configFromMap, configFromStream
from igs.utils.logging import errorPrintS

from vappio.instance.control import runSystemInstanceEx

from vappio.ec2 import control as ec2control


def cliParser():
    parser = optparse.OptionParser(usage='usage: %prog --host x --pipeline y [ -- options for pipeline]')

    parser.add_option('', '--conf', dest='conf', help='Name of config file to load')
    parser.add_option('', '--cluster', dest='cluster', help='Name of cluster to upload to (currently not used)')
    parser.add_option('', '--host', dest='host', help='Host of machine to upload to (will be deprecated once --cluster works')
    parser.add_option('', '--pipeline', dest='pipeline', help='Name of the pipeline')

    return parser

def cliMerger(cliOptions, args):
    if not cliOptions.host:
        raise MissingOptionError('Missing host option')

    if not cliOptions.pipeline:
        raise MissingOptionError('Missing pipeline option')

    return configFromMap({
        'cluster': cliOptions.cluster,
        'host': cliOptions.host,
        'pipeline': cliOptions.pipeline,
        'options': args
        }, configFromStream(open(cliOptions.conf)))

def getInstances(f):
    return [i for i in ec2control.listInstances() if f(i)]


def main(options):
    instances = getInstances(lambda i : i.publicDNS == options('host'))
    if not instances:
        raise Exception('Did not provide a valid host')

    mastInst = instances[0]
    cmd = ['runPipeline_remote.py', options('pipeline')] + options('options')
    runSystemInstanceEx(mastInst, ' '.join(cmd), None, errorPrintS, user='root', options=options('ssh.options'), log=True)    
        

if __name__ == '__main__':
    main(buildConfig(cliParser(), cliMerger))    

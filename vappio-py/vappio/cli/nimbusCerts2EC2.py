#!/usr/bin/env python
##
# A little tool to convert nimbus certs to EC2
import os
import optparse

from igs.utils.cli import buildConfig
from igs.utils.config import configFromMap
from vappio.nimbus.utils.convert import convertCert, convertKey, addJavaCert


def cliParser():
    parser = optparse.OptionParser(usage='usage: %prog [options]\n%prog will prompt for any variables not passed on the command line')

    parser.add_option('', '--in-cert', dest='in_cert', default=None,
                      help='Input certificate')
    parser.add_option('', '--out-cert', dest='out_cert', default=None,
                      help='Output certificate')
    parser.add_option('', '--in-key', dest='in_key', default=None,
                      help='Input key')
    parser.add_option('', '--out-key', dest='out_key', default=None,
                      help='Output key')
    parser.add_option('', '--java-cert-dir', dest='java_cert_dir', default=None,
                      help='Directory to put the jssecacerts file')
    parser.add_option('', '--java-cert-host', dest='java_cert_host', default=None,
                      help='Host for java certificate')
    parser.add_option('', '--java-cert-port', dest='java_cert_port', default=None,
                      help='Port for java certificate')

    return parser

def cliMerger(cliOptions, _args):
    return configFromMap(dict(in_cert=cliOptions.in_cert,
                              out_cert=cliOptions.out_cert,
                              in_key=cliOptions.in_key,
                              out_key=cliOptions.out_key,
                              java_cert_dir=cliOptions.java_cert_dir,
                              java_cert_host=cliOptions.java_cert_host,
                              java_cert_port=cliOptions.java_cert_port))



def promptIfNone(value, prompt):
    if value is None:
        return raw_input(prompt + ': ')
    else:
        return value

def main(options):
    values = {}
    for v, p in [('in_cert', 'Nimbus certificate file'),
                 ('out_cert', 'Converted EC2 cert file'),
                 ('in_key', 'Nimbus key file'),
                 ('out_key','Converted EC2 key file'),
                 ('java_cert_dir', 'Directory for java certificate'),
                 ('java_cert_host', 'Host for java cert'),
                 ('java_cert_port', 'Port for java cert')]:
        values[v] = promptIfNone(options(v), p)

    convertCert(open(values['in_cert']), open(values['out_cert'], 'w'))
    convertKey(values['in_key'], values['out_key'])
    addJavaCert(values['java_cert_dir'], values['java_cert_host'], int(values['java_cert_port']))

    print 'The certificates have been successfully convert, please set the following variables:'
    print 'export EC2_JVM_ARGS="-Djavax.net.ssl.trustStore=%s"' % os.path.join(values['java_cert_dir'], 'jssecacerts')
    print 'export EC2_CERT=' + values['out_cert']
    print 'export EC2_PRIVATE_KEY=' + values['out_key']

if __name__ == '__main__':
    options = buildConfig(cliParser(), cliMerger)
    main(options)

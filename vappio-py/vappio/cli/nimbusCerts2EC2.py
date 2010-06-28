#!/usr/bin/env python
##
# A little tool to convert nimbus certs to EC2
import os

from igs.utils.cli import buildConfigN
from igs.utils.functional import identity
from vappio.nimbus.utils.convert import convertCert, convertKey, addJavaCert


OPTIONS = [
    ('in_cert', '', '--in-cert', 'Nimbus certificate file', identity),
    ('out_cert', '', '--out-cert', 'Converted EC2 cert file', identity),
    ('in_key', '', '--in-key', 'Nimbus key file', identity),
    ('out_key', '', '--out-key', 'Converted EC2 key file', identity),
    ('java_cert_dir', '', '--java-cert-dir', 'Directory for java certificate', identity),
    ('java_cert_host', '', '--java-cert-host', 'Host for java cert', identity),
    ('java_cert_port', '', '--java-cert-port', 'Port for java cert', identity)
    ]


def promptIfNone(value, prompt):
    if value is None:
        return raw_input(prompt + ': ')
    else:
        return value

def main(options, _args):
    values = {}
    for v, p in [(v, p) for v, _s, _l, p, _f in OPTIONS]:
        values[v] = promptIfNone(options(v), p)

    convertCert(open(values['in_cert']), open(values['out_cert'], 'w'))
    convertKey(values['in_key'], values['out_key'])
    addJavaCert(values['java_cert_dir'], values['java_cert_host'], int(values['java_cert_port']))

    print 'The certificates have been successfully convert, please set the following variables:'
    print 'export EC2_JVM_ARGS="-Djavax.net.ssl.trustStore=%s"' % os.path.join(values['java_cert_dir'], 'jssecacerts')
    print 'export EC2_CERT=' + values['out_cert']
    print 'export EC2_PRIVATE_KEY=' + values['out_key']

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS, usage='usage: %prog [options]\n%prog will prompt for any variables not passed on the command line', putInGeneral=False))

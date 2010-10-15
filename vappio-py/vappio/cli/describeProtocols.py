#!/usr/bin/env python
from igs.utils import cli
from igs.utils import functional as func

from vappio.webservice import protocol

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', cli.defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster', cli.defaultIfNone('local')),
    ('config_from_protocol', '-p', '--config-from-protocol', 'Create a config file from a protocol and print it to stdout', func.identity),
    ('config_options', '-c', '--config',
     'Specify a value to replace when outputing a config file. Can specify multiple i.e. -c input.PIPELINE_NAME=foo -c cluster.CLUSTER_NAME=bar',
     cli.defaultIfNone([]), cli.LIST)
    ]

def main(options, _args):
    if options('general.config_options') and not options('general.config_from_protocol'):
        raise cli.MissingOptionError('Must specify --config-from-protocol in ordr to use --config')

    protocols = protocol.describeProtocols(options('general.host'), options('general.name'))

    if not options('general.config_from_protocol'):
        for p in protocols:
            print '\t'.join(['PROTOCOL', p.name])
    else:
        protoIdx = func.find(lambda p : p.name == options('general.config_from_protocol'), protocols)
        if protoIdx is None:
            raise Exception('Must provide a valid protocol name')

        
        proto = protocols[protoIdx]
        kv = dict([v.split('=', 1) for v in options('general.config_options')])
        section = proto.config and proto.config[0][0].split('.', 1)[0] or ''
        print '[' + section + ']'
        for k, d in proto.config:
            if k.split('.', 1)[0] != section:
                section = k.split('.', 1)[0]
                print
                print '[' + section + ']'
                
            if 'display' in d and d['display']:
                print '#', d['display']
            if 'desc' in d and d['desc']:
                print '#', d['desc']
            if 'choices' in d:
                print '# Possible values:', ' '.join([str(f) for f in d['choices']])

            if k in kv:
                v = kv[k]
            elif 'default' in d:
                v = d['default']
            else:
                v = ''

            print k.split('.', 1)[1] + '=' + str(v)
            print

        
if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))

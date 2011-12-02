#!/usr/bin/env python
from igs.utils import cli
from igs.utils import functional as func

from vappio.webservice import protocol

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', cli.defaultIfNone('localhost')),
    ('cluster', '', '--cluster', 'Name of cluster', cli.defaultIfNone('local')),
    ('config_from_protocol', '-p', '--config-from-protocol', 'Create a config file from a protocol and print it to stdout', func.identity),
    ('config_options', '-c', '--config',
     'Specify a value to replace when outputing a config file. Can specify multiple i.e. -c input.PIPELINE_NAME=foo -c cluster.CLUSTER_NAME=bar',
     cli.defaultIfNone([]), cli.LIST),
    ('batch_mode', '', '--batch-mode', 'Want to run the protocol in batch mode', cli.defaultIfNone(False), cli.BINARY)
    ]

def main(options, _args):
    if options('general.config_options') and not options('general.config_from_protocol'):
        raise cli.MissingOptionError('Must specify --config-from-protocol in order to use --config')

    if not options('general.config_from_protocol'):
        protocols = protocol.listProtocols(options('general.host'), options('general.cluster'))
        for p in protocols:
            print '\t'.join(['PROTOCOL', p['protocol']])
    else:
        proto = protocol.protocolConfig(options('general.host'),
                                        options('general.cluster'),
                                        options('general.config_from_protocol'),
                                        options('general.batch_mode'))[0]

        kv = dict([v.split('=', 1) for v in options('general.config_options')])
        section = proto and proto['config'][0]['name'].split('.', 1)[0] or ''
        print '[' + section + ']'
        for d in proto['config']:
            k = d['name']
            if k.split('.', 1)[0] != section:
                section = k.split('.', 1)[0]
                print
                print '[' + section + ']'
                
            if 'display' in d and d['display']:
                print '#', d['display']
            if 'desc' in d and d['desc']:
                print '#', d['desc']
            if 'type_params' in d and 'choices' in d['type_params']:
                print '# Possible values:', ' '.join([str(f) for f in d['type_params']['choices']])

            if k in kv:
                v = kv.pop(k)
            elif 'default' in d:
                v = d['default']
            else:
                v = ''

            print k.split('.', 1)[1] + '=' + str(v)
            print

        if kv:
            print '[]'
            for k, v in kv.iteritems():
                print '%s=%s' % (k, v)

        
if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))

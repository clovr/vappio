#!/usr/bin/env python
##
# Provides useful URLs and other information about the cluster

from igs.utils import cli
from igs.utils.functional import identity

from vappio.webservice.cluster import listClusters

OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', cli.defaultIfNone('localhost')),
    ('cluster', '', '--cluster', 'Name of cluster', cli.defaultIfNone('local')),
    ('list', '-l', '--list', 'List all clusters', cli.defaultIfNone(False), cli.BINARY)
    ]

URL = '/vappio/clusterInfo_ws.py'

def instanceToList(i):
    if i:
        return [i['instance_id'] or i['spot_request_id'] or 'Undefined',
                i['public_dns'] or 'Undefined',
                i['state'] or 'Undefined']
    else:
        return ['None']

def returnEmptyDictIfNone(d, k):
    if d[k] is None:
        return {}
    else:
        return d[k]

def main(options, _args):
    if not options('general.list'):
        cluster = listClusters(options('general.host'),
                               {'cluster_name': options('general.cluster')})[0]


        print '\t'.join(['STATE'] + [cluster['state']])
        print '\t'.join(['MASTER'] + instanceToList(cluster['master']))
        for e in cluster['exec_nodes']:
            print '\t'.join(['EXEC'] + instanceToList(e))
        for e in cluster['data_nodes']:
            print '\t'.join(['DATA'] + instanceToList(e))

        print '\t'.join(['GANGLIA', 'http://%s/ganglia' % returnEmptyDictIfNone(cluster, 'master').get('public_dns', '')])
        print '\t'.join(['ERGATIS', 'http://%s/ergatis' % returnEmptyDictIfNone(cluster, 'master').get('public_dns', '')])
        print '\t'.join(['SSH', 'ssh %s %s@%s' % (cluster.get('config', {}).get('ssh.options', ''),
                                                  cluster.get('config', {}).get('ssh.user', ''),
                                                  returnEmptyDictIfNone(cluster, 'master').get('public_dns', ''))])

    else:
        for c in listClusters(options('general.host')):
            print '\t'.join(['CLUSTER', c['cluster_name']])

if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))

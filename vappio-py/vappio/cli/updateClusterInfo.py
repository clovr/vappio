#! /usr/bin/env python
##
# This loads the local cluster and if it is an ec2 cluster it updates its information
# The main thing it updates right now is the state of the child instances

from igs.utils import cli

from vappio.cluster.persist_mongo import load, dump

OPTIONS = []


def main(options, _args):
    cluster = load('local')

    if cluster.ctype.NAME == 'EC2':
        cluster.dataNodes = cluster.ctype.updateInstances(cluster.dataNodes)
        cluster.execNodes = cluster.ctype.updateInstances(cluster.execNodes)

        dump(cluster)
    


if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))

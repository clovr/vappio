#! /usr/bin/env python
##
# This loads the local cluster and if it is an ec2 cluster it updates its information
# The main thing it updates right now is the state of the child instances

from igs.utils import cli
from igs.utils import logging

from vappio.cluster.persist_mongo import load, dump

OPTIONS = [
    ('debug', '', '--debug', 'Debugging', cli.defaultIfNone(False), True),
    ]


def main(options, _args):
    logging.DEBUG = options('general.debug')
    
    cluster = load('local')

    if cluster.ctype.NAME == 'EC2':
        cluster.dataNodes = cluster.ctype.updateInstances(cluster.dataNodes)
        cluster.execNodes = cluster.ctype.updateInstances(cluster.execNodes)

        logging.debugPrint(lambda : 'Dumping new cluster')
        dump(cluster)
    


if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))

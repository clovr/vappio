#! /usr/bin/env python
##
# This loads the local cluster and if it is an ec2 cluster it updates its information
# The main thing it updates right now is the state of the child instances

from igs.utils import cli
from igs.utils import logging

from vappio.cluster import control as cluster_ctl

OPTIONS = [
    ('debug', '', '--debug', 'Debugging', cli.defaultIfNone(False), True),
    ]


def main(options, _args):
    logging.DEBUG = options('general.debug')
    
    cluster = cluster_ctl.loadCluster('local')

    if cluster.ctype.NAME in ['EC2', 'Nimbus', 'DIAG']:
        cluster = cluster.update(dataNodes=cluster.ctype.updateInstances(cluster.credInst, cluster.dataNodes),
                                 execNodes=cluster.ctype.updateInstances(cluster.credInst, cluster.execNodes))

        logging.debugPrint(lambda : 'Dumping new cluster')
        cluster_ctl.saveCluster(cluster)
    


if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))

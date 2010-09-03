#!/usr/bin/env python
from igs.utils import cli
from igs.utils import functional as func

from vappio.webservice import pipeline

OPTIONS = [
    ('name', '', '--name', 'Name of cluster to run on', cli.notNone),
    ('pipeline', '', '--pipeline-name', 'Name of pipeline to run against', func.identity),
    ('conf', '-c', '--conf', 'Add config options, multiple allowed in style -c key=value -c key=value',
     func.identity, cli.LIST)
    ]


def main(options, _args):
    pass


if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS, usage='%prog --name=cluster [options] "metric1 | metric2 | .. | metricn"\nQuotes are important'))

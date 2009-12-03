##
# Simple script to seed SGE
import sys

from igs.utils.commands import runSystemEx
from igs.utils.config import replaceStr

from vappio.instance.config import configFromStream

def runSystemExC(conf, cmd):
    cmd = replaceStr(cmd, conf)
    runSystemEx(cmd)


def main(options):
    conf = configFromStream('/tmp/machine.conf')
    runSystemExC(conf, '${sge.root}/bin/${sge.arch}/qconf -aattr queue hotlist %s %s' % (sys.argv[1], sys.argv[2]))


if __name__ == '__main__':
    main(None)
    

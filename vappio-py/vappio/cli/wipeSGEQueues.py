#!/usr/bin/env python
##
# A simple script to wipe SGE queues
from igs.utils.commands import runSingleProgram
from igs.utils.config import replaceStr

from vappio.instance.config import configFromStream


def runSingleProgramEx(conf, cmd, stdoutf, stderrf):
    cmd = replaceStr(cmd, conf)
    exitCode = runSingleProgram(cmd, stdoutf, stderrf)
    if exitCode != 0:
        raise ProgramRunError(cmd, exitCode)


def runOnElements(query, exc):
    outp = []
    runSingleProgramEx(conf, '${sge.root}/bin/${sge.arch}/qconf ' + query, outp.append, None)
    hosts = ' '.join(outp)
    for h in hosts.split():
        runSingleProgramEx(conf, '${sge.root}/bin/${sge.arch}/qconf %s %s' %(exc, h), None, None)    
    
def main(options):
    conf = configFromStream('/tmp/machine.conf')
    runOnElements('-ss', '-ds')
    runOnElements('-sql', '-dq')
    runSingleProgramEx(conf, '${sge.root}/bin/${sge.arch}/qconf -kej ${MY_IP}', None, None)
    runOnElements('-sel', '-de')
    runOnElements('-sh', '-dh')
    runSingleProgramEx(conf, '${sge.root}/bin/${sge.arch}/qconf -dprj global', None, None)
    

if __name__ == '__main__':
    main(None)
    

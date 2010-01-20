#!/usr/bin/env python
##
# A simple script to wipe SGE queues
from igs.utils.commands import runSingleProgram, ProgramRunError
from igs.utils.config import replaceStr
from igs.utils.logging import errorPrint

from vappio.instance.config import configFromStream


def runSingleProgramEx(conf, cmd, stdoutf, stderrf):
    cmd = replaceStr(cmd, conf)
    exitCode = runSingleProgram(cmd, stdoutf, stderrf)
    if exitCode != 0:
        raise ProgramRunError(cmd, exitCode)


def runOnElements(conf, query, exc):
    try:
        outp = []
        runSingleProgramEx(conf, '${sge.root}/bin/${sge.arch}/qconf ' + query, outp.append, None)
        hosts = ' '.join(outp)
        for h in hosts.split():
            runSingleProgramEx(conf, '${sge.root}/bin/${sge.arch}/qconf %s %s' %(exc, h), None, None)
    except ProgramRunError, err:
        errorPrint(str(err))
    
def main(options):
    conf = configFromStream(open('/tmp/machine.conf'))
    runOnElements(conf, '-ss', '-ds')
    runOnElements(conf, '-sql', '-dq')
    try:
        runSingleProgramEx(conf, '${sge.root}/bin/${sge.arch}/qconf -kej ${MY_IP}', None, None)
    except ProgramRunError, err:
        errorPrint(str(err))
    runOnElements(conf, '-sel', '-de')
    runOnElements(conf, '-sh', '-dh')
    try:
        runSingleProgramEx(conf, '${sge.root}/bin/${sge.arch}/qconf -dprj global', None, None)
    except ProgramRunError, err:
        errorPrint(str(err))
    

if __name__ == '__main__':
    main(None)
    

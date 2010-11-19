import sys

from twisted.internet import reactor

from igs_tx.utils import commands

d = commands.runProcess(['date'], stdoutf=None, stderrf=None, expected=[0])

d.addCallback(lambda _ : sys.stdout.write('FINISHED!\n')).addErrback(lambda r : sys.stdout.write('errrr??? %d\n' % r.exitCode)).addCallback(lambda _ : reactor.stop())

reactor.run()

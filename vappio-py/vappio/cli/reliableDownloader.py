#! /usr/bin/env python
import sys
import os
import time
import signal

from igs.utils import logging
from igs.utils import cli
from igs.utils import commands
from igs.utils import functional as func
from igs.threading import threads

OPTIONS = [
    ('base_dir', '-b', '--base-dir', 'Base directory to download into', cli.defaultIfNone('.')),
    ('min_rate', '-m', '--min-rate', 'Minimum download rate in kilobytes per second', func.compose(int, cli.notNone)),
    ('tries', '-t', '--tries', 'Number of download attempts to make', func.compose(int, cli.defaultIfNone('3'))),
    ('debug', '-d', '--debug', 'Turn debug on', cli.defaultIfNone(False), True)
    ]


SAMPLE_RATE = 3

MAX_SAMPLE_SIZE = 10

def runDownloader(chan):
    pr, rchan = chan.receive()
    try:
        commands.runProgramRunnerEx(pr)
        rchan.send(None)
    except Exception, err:
        rchan.sendError(err)

def getSizeOfDir(d):
    stdoutL = []
    commands.runSingleProgramEx('du -ks ' + d,
                                stdoutf=stdoutL.append,
                                stderrf=None,
                                log=False)
    return int(''.join(stdoutL).split()[0])
    
        
def monitorDownload(pr, downloaderChan, downloadDir, minRate):
    sizeSamples = []
    while True:
        baseSize = getSizeOfDir(downloadDir)
        time.sleep(SAMPLE_RATE)
        ##
        # If the program exited and exited correctly, then we're good
        # otherwise take another sample size and see if we should terminate
        if pr.exitCode is not None:
            ret = downloaderChan.receive()
            return True
        else:
            currentSize = getSizeOfDir(downloadDir) - baseSize
            logging.debugPrint(lambda : 'Download rate: %d' % (currentSize/SAMPLE_RATE))
            sizeSamples.append(currentSize/SAMPLE_RATE)
            if len(sizeSamples) > MAX_SAMPLE_SIZE:
                sizeSamples.pop(0)

            if len(sizeSamples) >= MAX_SAMPLE_SIZE and sum(sizeSamples)/len(sizeSamples) < minRate:
                logging.debugPrint(lambda : 'Average Rate: %d' % (sum(sizeSamples)/len(sizeSamples)))
                os.kill(pr.pipe.pid, signal.SIGTERM)
                try:
                    downloaderChan.receive()
                except:
                    pass
                return False


def attemptDownload(options, url):
    pr = commands.ProgramRunner('wget -c --quiet -P %s %s' % (options('general.base_dir'),
                                                              url),
                                stdoutf=sys.stdout.write,
                                stderrf=sys.stderr.write,
                                log=True)

    downloaderChan = threads.runThreadWithChannel(runDownloader).channel.sendWithChannel(pr)
    ##
    # sleep for a second so the program can run
    time.sleep(1)

    logging.debugPrint(lambda : 'Downloading with a minimum acceptable rate of %d' % options('general.min_rate'))

    return monitorDownload(pr, downloaderChan, options('general.base_dir'), options('general.min_rate'))

    
            
def main(options, args):
    logging.DEBUG = options('general.debug')
        
    if not args:
        raise Exception('Must pass URL')

    url = args[0]

    tries = options('general.tries')
    
    while tries > 0:
        if not attemptDownload(options, url):
            logging.debugPrint(lambda : 'Download failed, trying again. %d' % tries)
            tries -= 1
        else:
            return

    raise Exception('Download failed')
        


if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS))

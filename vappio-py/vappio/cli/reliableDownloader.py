#! /usr/bin/env python
import sys
import os
import time
import signal
import Queue
import urlparse
import glob

from igs.utils import logging
from igs.utils import cli
from igs.utils import commands
from igs.utils import functional as func
from igs.threading import threads

OPTIONS = [
    ('base_dir', '-b', '--base-dir', 'Base directory to download into', cli.defaultIfNone('.')),
    ('min_rate', '-m', '--min-rate', 'Minimum download rate in kilobytes per second', func.compose(int, cli.notNone)),
    ('tries', '-t', '--tries', 'Number of download attempts to make', func.compose(int, cli.defaultIfNone('3'))),
    ('max_threads', '', '--max-threads', 'Maximum number of threads to download at once', func.compose(int, cli.defaultIfNone('3'))),
    ('continue_download', '-c', '--continue', 'Continue the download.  Default is to download everything from scratch', cli.defaultIfNone(False), True),
    ('debug', '-d', '--debug', 'Turn debug on', cli.defaultIfNone(False), True)
    ]


##
# How many seconds each sample should be
SAMPLE_RATE = 5

MAX_SAMPLE_SIZE = 10

def runDownloader(chan):
    pr, rchan = chan.receive()
    try:
        commands.runProgramRunnerEx(pr)
        logging.debugPrint(lambda : 'Successfully completed download')
        rchan.send(None)
    except Exception, err:
        logging.debugPrint(lambda : 'Download failed for unknown reason')
        rchan.sendError(err)

def getSizeOfFiles(files):
    stdoutL = []
    commands.runSingleProgramEx('du -kcs ' + ' '.join(files),
                                stdoutf=stdoutL.append,
                                stderrf=None,
                                log=False)
    return int(stdoutL[-1].split()[0])
    
        
def monitorDownload(pr, downloaderChan, baseDir, url, minRate):
    sizeSamples = []
    while True:
        baseSize = getSizeOfFiles(getDownloadFilenames(baseDir, url))
        time.sleep(SAMPLE_RATE)
        ##
        # If the program exited and exited correctly, then we're good
        # otherwise take another sample size and see if we should terminate
        if pr.exitCode is not None:
            ret = downloaderChan.receive()
            return True
        else:
            currentSize = getSizeOfFiles(getDownloadFilenames(baseDir, url)) - baseSize
            logging.debugPrint(lambda : 'Download rate: %8d - %s' % (currentSize/SAMPLE_RATE, getUrlFilename(url)))
            size = currentSize/SAMPLE_RATE
            if size < 0:
                size = 0
            sizeSamples.append(size)
            if len(sizeSamples) > MAX_SAMPLE_SIZE:
                sizeSamples.pop(0)

            if len(sizeSamples) >= MAX_SAMPLE_SIZE and sum(sizeSamples)/len(sizeSamples) < minRate:
                logging.debugPrint(lambda : 'Average Rate: %8d - %s' % (sum(sizeSamples)/len(sizeSamples), getUrlFilename(url)))
                os.kill(pr.pipe.pid, signal.SIGTERM)
                ##
                # Give it a second to finish up whatever it's doing
                time.sleep(2)
                try:
                    downloaderChan.receive()
                except:
                    pass
                return False


def attemptDownload(options, url):
    cmd = ['wget', '--quiet', '-P', options('general.base_dir')]
    if options('general.continue_download'):
        cmd.append('-c')

    cmd.append(url)
    pr = commands.ProgramRunner(' '.join(cmd),
                                stdoutf=sys.stdout.write,
                                stderrf=sys.stderr.write,
                                log=True)

    downloaderChan = threads.runThreadWithChannel(runDownloader).channel.sendWithChannel(pr)
    ##
    # sleep for a second so the wget can run
    time.sleep(1)

    logging.debugPrint(lambda : 'Downloading with a minimum acceptable rate of %d' % options('general.min_rate'))

    return monitorDownload(pr, downloaderChan, options('general.base_dir'), url, options('general.min_rate'))


def getUrlFilename(url):
    parsed = urlparse.urlparse(url)
    _, fname = os.path.split(parsed.path)
    return fname
    

def getDownloadFilenames(baseDir, url):
    fname = getUrlFilename(url)
    return glob.glob(os.path.join(baseDir, fname))

def deleteDownloadedFiles(baseDir, url):
    files = getDownloadFilenames(baseDir, url)
    for f in files:
        logging.debugPrint(lambda : 'Deleting: ' + f)
        os.remove(f)
    

def validMD5(options, url, md5):
    if md5 is not None:
        stdout = []
        files = getDownloadFilenames(options('general.base_dir'), url)
        files.sort()
        commands.runSingleProgramEx('cat %s | md5sum' % ' '.join(files), stdoutf=stdout.append, stderrf=None, log=True)
        newMd5 = stdout[-1].split(' ', 1)[0]
        logging.debugPrint(lambda : 'Comparing %s to %s' % (md5, newMd5))
        return md5 == newMd5
    else:
        return True
        
def downloadUrls(chan):
    (options, queue), rchan = chan.receive()

    ##
    # Loop until queue is empty
    try:
        while True:
            url, md5 = queue.get_nowait()


            ##
            # Skip all this if it's already been downloaded
            if md5 and validMD5(options, url, md5):
                rchan.send((url, True))
                continue
            
            if not options('general.continue_download'):
                logging.debugPrint(lambda : 'Deleting any files that already exist')
                deleteDownloadedFiles(options('general.base_dir'), url)
                time.sleep(1)
                
            tries = options('general.tries')
            try:
                while (not attemptDownload(options, url) or not validMD5(options, url, md5)) and tries > 0:
                    logging.debugPrint(lambda : 'Download failed, trying again. %d' % tries)
                    if not options('general.continue_download'):
                        logging.debugPrint(lambda : 'Deleting downloaded files')
                        deleteDownloadedFiles(options('general.base_dir'), url)
                        time.sleep(1)
                    tries -= 1

                if tries <= 0:
                    rchan.send((url, False))
                else:
                    rchan.send((url, True))

            except Exception, err:
                logging.errorPrint('Download failed: ' + str(err))
                rchan.send((url, False))
                
    except Queue.Empty:
        rchan.send(None)

    


def main(options, args):
    logging.DEBUG = options('general.debug')

    queue = Queue.Queue()
    if not args:
        for line in sys.stdin:
            md5, url = line.split(' ', 1)
            url = url.strip()
            queue.put((url, md5))
    else:
        for url in args:
            queue.put((url, None))

    retChans = [threads.runThreadWithChannel(downloadUrls).channel.sendWithChannel((options, queue)) for _ in range(options('general.max_threads'))]

    successUrls = []
    failedUrls = []
    for c in retChans:
        ret = c.receive()
        while ret is not None:
            url, succ = ret
            if succ:
                successUrls.append(url)
            else:
                failedUrls.append(url)

            ret = c.receive()

    if failedUrls:
        for url in failedUrls:
            logging.errorPrint(url)

        ##
        # If any URLs failed, exit with fail
        sys.exit(1)
    

if __name__ == '__main__':
    sys.exit(main(*cli.buildConfigN(OPTIONS)))

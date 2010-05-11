#!/usr/bin/env python
##
# This is meant to look and feel almost exactly like the ncbi-blastall program.
# This will require a few extra options though related around how to handle a cluster.
#
# The major differences between this and ncbi-blastall:
# --auto=# or --cluster=name - This can either create a cluster, run the jobs on it all on its own
#                              or use an existing cluster.  In the case of --auto, the cluster will
#                              be started and terminated automatically after the data has been downloaded.
#                              --auto take the number of worker nodes to start up as an argument
#                              In the case of --cluster, the cluster will not be started or terminated, just
#                              used to run the pipeline.
# -d - This is the refrence db to use.  This option has been modified a little bit.  Because we don't want
#      the user to have to upload reference databases all the time we allow them to specify a tag that will
#      handle the reference database for them.  However, the user may want to upload their own refrence database
#      rather than use one of the ref dbs we provide.  In order to make this as seamless as possible we want to
#      provide the same option for both.  As a result, if -d is an absolute path (starts with /) then we assume
#      the user is specifying a path to their db, in which case we tag it and upload it.  Otherwise if the
#      option for -d does not start with a '/' we assume they are specifying a tag name.
#
# This is a bit more strict than the standard blastall because it involves possibly spending a fair amount of money
# only to have your run fail if you forgot something it tries to make it hard to make an error
import sys
import os
import time

from igs.utils import logging
from igs.utils.logging import debugPrint, logPrint, errorPrint
from igs.utils.cli import MissingOptionError
from igs.utils.functional import tryUntil
from igs.utils.commands import runSystemEx

from vappio.webservice.tag import queryTag, tagData, uploadTag
from vappio.webservice.cluster import startCluster, listClusters, terminateCluster
from vappio.webservice.pipeline import runPipeline, pipelineStatus, downloadPipelineOutput

from vappio.tasks.task import TASK_FAILED
from vappio.tasks.utils import blockOnTask

NUM_TRIES = 60

def progress():
    """Little function to wait and put dots showing progress"""
    sys.stdout.write('.')
    sys.stdout.flush()
    time.sleep(30)

def printUsage():
    raise Exception('Implement me!')

def blockOnTaskAndFail(name, taskName, errMsg):
    state = blockOnTask('localhost', name, taskName)
    if state == TASK_FAILED:
        raise Exception(errMsg)


def get_input(prompt, f):
    inp = raw_input(prompt)
    while not f(inp):
        inp = raw_input(prompt)
    return inp

def extractOption(args, shortOpt, longOpt, needsArgument=False):
    """
    shortOpt and longOpt should contain - and -- repsectively if they should have it.
    Either can be None.

    It starts with short name then long name.  For each it first checks to see if the option
    just exists.  If not it check to see if it exists with a = in it, if needsArgument is
    specified.

    If it finds it, True is returned if needsArgument is False.  If needsArgument is True
    it checks to see if the found argument has a '=' in it, otherwise it looks for it in the
    next position in the argument list.  It returns the argument value

    False is returned if it cannot be found
    """
    for idx, arg in enumerate(args):
        if (arg == shortOpt or arg == longOpt) and needsArgument:
            return args[idx + 1]
        elif (arg == shortOpt or arg == longOpt) and not needsArgument:
            return True
        elif (shortOpt and arg.startswith(shortOpt + '=') or longOpt and arg.startswith(longOpt + '=')) and needsArgument:
            return arg.split('=', 1)[1]

    return False

def validateInput(args):
    if not extractOption(args, None, '--auto', True) and not extractOption(args, None, '--cluster', True):
        raise MissingOptionError('Must provide --auto or --cluster')

    if not extractOption(args, '-p', None, True):
        raise MissingOptionError('Must provide a program name')

    if extractOption(args, '-p', None, True) not in ['blastn',
                                                     'blastp',
                                                     'blastx',
                                                     'tblastn',
                                                     'tblastx']:
        raise MissingOptionError('Must provide a valid program name')
    
    if not extractOption(args, '-i', None, True):
        raise MissingOptionError('Must provide an input file')

    if not extractOption(args, '-o', None, True):
        raise MissingOptionError('Must provide an output directory')

    if not extractOption(args, '-d', None, True):
        raise MissingOptionError('Must provide a reference database file name or tag name')

    if not extractOption(args, '-e', None, True):
        raise MissingOptionError('Must provide an expect value')

def tagExists(cluster, tagName):
    """
    Determine if a tag exists
    """
    try:
        return len(queryTag('localhost', cluster, tagName)('files')) > 0
    except:
        return False


def clusterExists(clusterName):
    return clusterName in listClusters('localhost')


def tagInputIfNeeded(inputFile):
    inputTagName = os.path.basename(inputFile)
    if not tagExists('local', inputTagName):
        debugPrint(lambda : 'Tagging input file: ' + inputFile)
        taskName = tagData('localhost',
                           'local',
                           inputTagName,
                           os.path.dirname(inputFile),
                           [inputFile],
                           False,
                           False,
                           False,
                           True)
        blockOnTaskAndFail('local', taskName, 'Tagging input failed')
    else:
        debugPrint(lambda : 'Input tag exists')

def tagDatabaseFiles(databasePath):
    """
    Takes a path to a database like blast expects it.  It then goes through
    the directory finding all files that start with databasePath + '.' and
    tags them

    """
    tagName = os.path.basename(databasePath) + '_db'
    baseName = os.path.basename(databasePath)
    dirName = os.path.dirname(databasePath)
    if not tagExists('local', tagName):
        debugPrint(lambda : 'Tagging database: ' + databasePath)
        taskName = tagData('localhost',
                           'local',
                           tagName,
                           dirName,
                           [os.path.join(dirName, f) for f in os.listdir(dirName) if f.startswith(baseName + '.')],
                           False,
                           False,
                           False,
                           True)
        blockOnTaskAndFail('local', taskName, 'Tagging input failed')
    return tagName


def makeClusterIfNeeded(numNodes, autoClusterName, alreadyClusterName):
    """
    autoClusterName - Name of the cluster if we decide to make one ourselves
    numNodes - How many exec nodes
    alreadyClusterName - Name of cluster to use if we decide to not make one ourselves
    """
    ##
    # numNodes could be 0, we only want to do this path if it exlicitly is
    # not False
    if numNodes is not False:
        if clusterExists(autoClusterName):
            debugPrint(lambda : 'Cluster already exists, using it')
        else:
            debugPrint(lambda : 'Starting cluster...')
            taskName = startCluster('localhost',
                                    autoClusterName,
                                    'clovr.conf',
                                    numNodes,
                                    'ec2',
                                    False)
            blockOnTaskAndFail('local', taskName, 'Error starting cluster')
        return autoClusterName
    else:
        if not clusterExists(alreadyClusterName):
            raise MissingOptionError('Cluster %s does not exist, do you want --auto?' % alreadyClusterName)
        return alreadyClusterName


def removeCustomOptions(args):
    """
    This removes all custom options and returns a new copy.  Custome options
    are defined as those that this program will muck with so:

    --auto <opt>
    --cluster <opt>
    -i <opt>
    -d <opt>
    -o <opt>
    --seqs_per_file <opt>
    --debug
    """

    wantArg = False
    retArgs = []
    for a in args:
        if not wantArg:
            if a in ['--auto', '--cluster', '-i', '-d', '-o', '-e', '--seqs_per_file']:
                wantArg = True
            elif a == '--debug' or a.startswith('--cluster=') or a.startswith('--auto=') or a.startswith('--seqs_per_file'):
                pass
            else:
                retArgs.append(a)
        else:
            wantArg = False

    return retArgs

            
def main(_options, args):
    ##
    # Because we are trying to mimic another program we have to do some funky work
    # with the options.  We also want to do some kind of validation of the options
    # so they don't bring up a cluster and try to run it only to find out it
    # has errored out.


    args = args[1:]

    if not args or args == ['--help']:
        printUsage()
        return

    if extractOption(args, None, '--debug'):
        logging.DEBUG = True
    
    try:
        validateInput(args)
        ##
        # make autoNodes the integer value of whatever is input or false
        autoNodes = extractOption(args, None, '--auto', True) and int(extractOption(args, None, '--auto', True))
        clusterName = extractOption(args, None, '--cluster', True)
        inputFile = extractOption(args, '-i', None, True)
        outputDir = extractOption(args, '-o', None, True)
        databasePath = extractOption(args, '-d', None, True)
        expectValue = extractOption(args, '-e', None, True)
        seqsPerFile = extractOption(args, None, '--seqs_per_file', True)

        try:
            seqsPerFile = seqsPerFile is not False and int(seqsPerFile)
        except ValueError:
            raise MissingOptionError('You must give an integer value for seqs per file')

        if autoNodes and clusterName:
            raise MissingOptionError('Can only specify --auto OR --cluster, not both')
        
        ##
        # Check that input tag exists
        inputTagName = os.path.basename(inputFile)
        tagInputIfNeeded(inputFile)

        ##
        # Check if input is a tag name or a file (starts with a '/')
        if databasePath[0] == '/':
            databaseTagName = tagDatabaseFiles(databasePath)
        else:
            ##
            # We can't use tagExists here because tagExists
            # checks to see if the tag has files associated
            # with it.  The user could be using a phantom
            # tag which won't have files associated with it until
            # it is uploaded.  So here we just do a quick check
            # to see if queryTag returns anything valid
            # if it does then at least a tag by that name
            # exists. Otherwise there is an error
            try:
                queryTag('localhost', 'local', databasePath)
                ##
                # If a success, then set the tagname to the path
                databaseTagName = databasePath
            except:
                raise MissingOptionError('Database tag does not exist locally')



        debugPrint(lambda : 'Checking to see if the cluster exists')
        ##
        # Want to create a cluster name that will be the same between runs
        # So we can just restart the script on failure
        clusterName = makeClusterIfNeeded(autoNodes, inputTagName + '-' + databaseTagName, clusterName)

        debugPrint(lambda : 'Uploading tags to the cluster')
        uploadTasks = []
        ##
        # Upload the tags and wait for them to be complete
        if not tagExists(clusterName, inputTagName):
            uploadTasks.append(uploadTag('localhost', inputTagName, 'local', clusterName, True))

        if not tagExists(clusterName, databaseTagName):
            uploadTasks.append(uploadTag('localhost', databaseTagName, 'local', clusterName, True))

        for t in uploadTasks:
            blockOnTaskAndFail('local', t, 'Error uploading tasks')

        print
        
        ##
        # Remove args specific to this script
        blastArgs = ' '.join(removeCustomOptions(args))

        pipelineName = inputTagName + '-' + databaseTagName
        debugPrint(lambda : 'Checking to see if pipeline is running...')
        if not pipelineStatus('localhost', clusterName, lambda p : p['name'] == pipelineName):
            debugPrint(lambda : '%s is not running, running now' % pipelineName)
            pipelineArgs = ['--OTHER_OPTS=' + blastArgs,
                            '--INPUT_FILE_LIST=' + inputTagName,
                            '--REF_DB_PATH=' + databaseTagName,
                            '--EXPECT=' + expectValue]
            if seqsPerFile is not False:
                pipelineArgs.append('--SEQS_PER_FILE=' + str(seqsPerFile))

            runPipeline('localhost', clusterName, 'clovr_blastall', pipelineName, pipelineArgs)

        debugPrint(lambda : 'Waiting for pipeline to finish...')
        pipelineInfo = pipelineStatus('localhost', clusterName, lambda p : p['name'] == pipelineName)[0]
        while pipelineInfo['state'] not in ['complete', 'failed', 'error']:
            for i in range(10):
                sys.stdout.write('.')
                sys.stdout.flush()
                time.sleep(5)
            pipelineInfo = pipelineStatus('localhost', clusterName, lambda p : p['name'] == pipelineName)[0]
            sys.stdout.write('\r                  \r')
            sys.stdout.flush()

        print
        
        if pipelineInfo['state'] == 'complete':
            debugPrint(lambda : 'Pipeline finished successfully, downloading')
            taskName = downloadPipelineOutput('localhost', clusterName, pipelineName, outputDir, True)
            debugPrint(lambda : 'Downloading pipeline...')
            downloadName = os.path.join(outputDir, pipelineName + '_output.tar.gz')
            time.sleep(10)
            blockOnTaskAndFail('local', taskName, 'Failed to download file')
            logPrint('Your pipeline is downloaded to %s ,  Enjoy' % downloadName)
            if autoNodes is not False:
                logPrint('Terminating cluster...')
                terminateCluster('localhost', clusterName, True)
            else:
                print
                print '*' * 40
                print 'Do not forget that you need to manually terminate your cluster when you are done'
                print 'You can terminate your cluster with the following command:'
                print 'terminateCluster.py --name=' + clusterName
        else:
            errorPrint('The pipeline failed!!!!')

            print
            print '*' * 40
            print 'Your pipeline failed! Would you like to TERMINATE the cluster?'
            print 'If you choose Y then the cluster will be destroyed and all of your data'
            print 'on it will be deleted.  If you choose N the cluster will be left up but'
            print 'you will have to remember to terminate it by running the following command:'
            print 'terminateCluster.py --name=' + clusterName
            if get_input('(Y/N)', lambda i : i in ['Y', 'N']) == 'Y':
                logPrint('Terminating cluster...')
                terminateCluster('localhost', clusterName, True)
            else:
                print
                print '*' * 40
                print 'You have elected to NOT terminate the cluster.'
                print 'Remember you MUST terminate your the cluster manually when you are done.'
                print 'You can terminate the cluster by running:'
                print 'terminateCluster.py --name=' + clusterName
        
            
    except MissingOptionError, err:
        print 'Missing an option:'
        print err
        


if __name__ == '__main__':
    main(None, sys.argv)

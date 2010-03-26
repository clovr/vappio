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

from igs.utils import logging
from igs.utils.logging import debugPrint
from igs.utils.cli import MissingOptionError
from igs.utils.functional import tryUntil
from igs.utils.commands import runSystemEx

from vappio.webservices.files import queryTag, tagData, uploadTag
from vappio.webservices.cluster import listClusters, terminateCluster

def printUsage():
    raise Exception('Implement me!')

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
        return len(queryTag('localhost', cluster, tagName)) > 0
    except:
        return False


def clusterExists(clusterName):
    return clusterName in listClusters('localhost')


def tagInputIfNeeded(inputFile):
    inputTagName = os.path.basename(inputFile)
    if not tagExists('local', inputTagName):
        debugPrint(lambda : 'Tagging input file: ' + inputFile):
        tagData('localhost',
                'local',
                inputTagName,
                os.path.dirname(inputFile),
                [inputFile],
                False,
                False,
                False,
                False)
        tryUntil(50, lambda : time.sleep(30), lambda : tagExists('local', inputTagName))
    else:
        debugPrint(lambda : 'Input tag exists')

def tagDatabaseFiles(databasePath):
    """
    Takes a path to a database like blast expects it.  It then goes through
    the directory finding all files that start with databasePath + '.' and
    tags them
    """
    tagName = os.path.basename(databasePath)
    dirName = os.path.dirname(databasePath)
    if not tagExists('local', tagName):
        debugPrint(lambda : 'Tagging database: ' + databasePath)
        tagData('localhost',
                'local',
                tagName,
                dirName,
                [os.path.join(dirName, f) for f in os.listdir(dirName) if f.startswith(tagName + '.')],
                False,
                False,
                False,
                False)
        tryUntil(50, lambda : time.sleep(30), lambda : tagExists('local', tagName))


def makeClusterIfNeeded(autoClusterName, numNodes, alreadyClusterName):
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
            ##
            # Normally we would us a webservice call, but in this case the CLI
            # program already handles blocking and all that for us.  Once tasks
            # are working we can use a blocking function there instead
            cmd = ['startCluster.py',
                   '--name=' + autoClusterName,
                   '--num=' + str(autoNodes),
                   '--ctype=ec2',
                   '-b']
            runSystemEx(' '.join(cmd), log=logging.DEBUG)
        return autoClusterName
    else:
        if not clusterExists(alreadyClusterName):
            raise MissingOptionError('Cluster %s does not exist, do you want --auto?' % alreadyClusterName)
        return alreadyClusterName

        
def main(_options, args):
    ##
    # Because we are trying to mimic another program we have to do some funky work
    # with the options.  We also want to do some kind of validation of the options
    # so they don't bring up a cluster and try to run it only to find out it
    # has errored out.


    if not args or args == ['--help']:
        printUsage()
        return

    if extractOption(args, None, '--debug'):
        logging.DEBUG = True
    
    try:
        validateInput(args)
        autoNodes = int(extractOption(args, None, '--auto', True))
        clusterName = extractOption(args, None, '--cluster', True)
        inputFile = extractOption(args, '-i', None, True)
        outputDir = extractOption(args, '-o', None, True)
        databasePath = extractOption(args, '-d', None, True)

        if autoNodes and clusterName:
            raise MissingOptionError('Can only specify --auto OR --cluster, not both')
        
        ##
        # Check that input tag exists
        inputTagName = os.path.basename(inputFile)
        tagInputIfNeeded(inputFile)

        ##
        # Check if input is a tag name or a file (starts with a '/')
        if databasePath[0] == '/':
            databaseTagName = os.path.basename(databasePath)
            tagDatabaseFiles(databasePath)
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

        
        ##
        # Want to create a cluster name that will be the same between runs
        # So we can just restart the script on failure
        clusterName = makeClusterIfNeeded(autoNodes, inputTagName + '-' + databaseTagName, clusterName)
            
    except MissingOptionError, err:
        print 'Missing an option:'
        print err
        


if __name__ == '__main__':
    main(None, sys.argv)

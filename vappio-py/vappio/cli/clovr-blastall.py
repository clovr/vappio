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

from igs.utils.cli import MissingOptionError
from igs.utils import logging
from igs.utils.logging import debugPrint
from igs.utils.functional import tryUntil

from vappio.webservices.files import queryTag, tagData, uploadTag

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
    
    if not extractOption(args, '-i', None, True):
        raise MissingOptionError('Must provide an input file')

    if not extractOption(args, '-o', None, True):
        raise MissingOptionError('Must provide an output directory')

    if not extractOption(args, '-d', None, True):
        raise MissingOptionError('Must provide a reference database file name or tag name')

    if not extractOption(args, '-e', None, True):
        raise MissingOptionError('Must provide an expect value')

    

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
        autoNodes = extractOption(args, None, '--auto', True)
        clusterName = extractOption(args, None, '--cluster', True)
        inputFile = extractOption(args, '-i', None, True)
        outputDir = extractOption(args, '-o', None, True)
        databasePath = extractOption(args, '-d', None, True)

        inputTagName = os.path.basename(inputFile)
        try:
            queryTag('localhost', 'local', inputTagName)
            debugPrint('Input tag exists')
        except:
            debugPrint('Tagging input file')
            tagData('localhost',
                    'local',
                    inputTagName,
                    os.path.basedir(inputFile),
                    [inputFile],
                    False,
                    False,
                    False,
                    False)
            ##
            # oogly
            def _queryTag():
                try:
                    return len(queryTag('localhost', 'local', inputTagName)('files')) > 0
                except:
                    return False

            ##
            # keep try this 50 times, should be quick though
            tryUntil(50, lambda : time.sleep(30), _queryTag)
            
    except MissingOptionError, err:
        print 'Missing an option:'
        print err
        


if __name__ == '__main__':
    main(None, sys.argv)

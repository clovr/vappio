#!/usr/bin/env python
# This checks out or exports an object from a repository.  Repositories are kept in configuration files so it is easy to
# add them and map them to a name.  Right now this just supports SVN but the idea this could support another of repository
# types.  This takes care of downloading from a specific branch and deciding between a check out and an export.
#
# In the case of checkouts, not all repository systems allow one to check out a single file.  In this case the system will
# check out the top level directory to a defined location and symlink the file.
#
# This program is meant to try to be as concise as possible with as few dependencies as possible and to reasonably live inside
# a single source file.  This is because it is used fairly early in the build process so it needs to be bootstrapped.
#
# There are a few configuration files.  The first is the 'repositories' file which is a simple tab delimited file that looks like:
# <projectname> <repotype> <repourl>
#
# Example:
# vappio svn svn://vappio.sf.net/this/is/made/up
# recipes git git://github.net/also/made/up
#
# The next file is the 'branches' file.  This is a tab delimited file as well:
# <projectname> <branchname>
#
# Example:
# vappio branches/testing-branch
# recipes master
#
# Note, for SVN branches the entire branches/path is required.  This is because the same mechanism can be used to get tags as well, one could do:
# tags/good-release for a branch.  Git does not have this distinction from what I understand.
# It is an error if one tries to check out a file from a project and it is not in both 'repositores' and 'branches'.
#
# The next file is 'checkouts'.  This file is simple, it contains a one project name per line.  If a project name is specified in here
# it is checked out rather than just exported.
#
# The log file is generated by this script.  It logs all checkouts.  This is useful for a few purposes
# 1) A debug log of what has been checked out, what kind of checkout, and where
# 2) A way to replay the checkouts
# 3) The log can be analyzed, if any checkins need to happen they can be performed even if someone forgot that they checked out a certain file
#    and modified it.
#
# This file should rarely, if ever, be viewd by the an end user but for completeness (incase someone wants to process it) the format is
# tab delimited again:
# <projectname> <branchname> <checkout/export> <repopath> <outputpath>
#
# Example:
# vappio branches/testing-branch checkout foo/bar/baz /opt/foo-baz


import os
from igs.utils import commands
from igs.utils import cli
from igs.utils import functional as func
from igs.utils import logging

OPTIONS = [
    ('codir', '', '--co-dir',
     'Directory to put files in case of a check out.  If not set, defaults to $VAPPIO_CO_DIR, if that is not set defaults to /opt/co-dir',
     func.compose(cli.defaultIfNone('/opt/co-dir'), cli.defaultIfNone(os.getenv('VAPPIO_CO_DIR')))),
    ('branch', '-b', '--branch',
     'Override the branch specified in config files',
     func.identity),
    ('checkout', '', '--co', 'Force a checkout', func.identity, cli.BINARY),
    ('export', '', '--export', 'Force an export, mutually exclusive with --checkout', func.identity, cli.BINARY),
    ('config_dir', '-c', '--config-dir', 'Directory to look for config files, defaults to $VAPPIO_REPO_CONF',
     func.compose(cli.notNone, cli.defaultIfNone(os.getenv('VAPPIO_REPO_CONF')))),
    ('debug', '-d', '--debug', 'Turn debugging information on', func.identity, cli.BINARY),
    ]

##
# Misc useful functions
def logExport(configDir, repo, repoPath, outputPath, branch, exportType):
    open(os.path.join(configDir, 'log'),
         'a').write('\t'.join([repo.name,
                               branch,
                               exportType,
                               repoPath,
                               outputPath]) + '\n')
         

##
# Repository implementations
class Subversion:
    def checkout(self, options, repo, repoPath, outputPath, branch):
        fullPath = os.path.join(repo.repoUrl, branch, repoPath)
        stderr = []
        try:
            commands.runSingleProgramEx('svn co %s %s' % (fullPath, outputPath),
                                        stdoutf=None,
                                        stderrf=stderr.append,
                                        log=logging.DEBUG)
        except commands.ProgramRunError:
            if 'refers to a file, not a directory' in ''.join(stderr):
                tmpPath = os.path.dirname(os.path.join(options('general.codir'), repoPath))
                commands.runSystemEx('mkdir -p ' + tmpPath, log=logging.DEBUG)
                commands.runSingleProgramEx('svn co %s %s' % (os.path.dirname(fullPath), tmpPath),
                                            stdoutf=None,
                                            stderrf=logging.errorPrintS,
                                            log=logging.DEBUG)
                commands.runSystemEx('ln -s %s %s' % (os.path.join(options('general.codir'), repoPath),
                                                      outputPath),
                                     log=logging.DEBUG)
            else:
                for l in stderr:
                    logging.errorPrintS(l)
                raise

        logExport(options('general.config_dir'), repo, repoPath, outputPath, branch, CHECKOUT)

    
    def export(self, options, repo, repoPath, outputPath, branch):
        fullPath = os.path.join(repo.repoUrl, branch, repoPath)
        commands.runSingleProgramEx('svn export %s %s' % (fullPath, outputPath),
                                    stdoutf=None,
                                    stderrf=logging.errorPrintS,
                                    log=logging.DEBUG)
        logExport(options('general.config_dir'), repo, repoPath, outputPath, branch, EXPORT)


class Git:
    """
    Not implemented yet
    """
    pass

##
# Different types of exports
CHECKOUT = 'co'
EXPORT = 'export'

##
# Maps a repository type id to a class
REPOSITORY_MAP = {
    'svn': Subversion,
    'git': Git,
    }



def loadRepositories(configDir):
    """
    Returns a map of repos names to record objects identifying the repos.  Each record object contains:
    - name
    - rType (git, svn instantiated)
    - repoUrl
    - exportType
    - branch

    Everything but the logs is loaded here
    """
    repos = {}
    for line in (l for l in open(os.path.join(configDir, 'repositories')) if l.strip()):
        repoName, repoType, repoUrl = line.strip().split('\t')
        repos[repoName] = func.Record(name=repoName,
                                      rType=REPOSITORY_MAP[repoType](),
                                      repoUrl=repoUrl,
                                      exportType=EXPORT)

    branches = []
    for line in (l for l in open(os.path.join(configDir, 'branches')) if l.strip()):
        repoName, repoBranch = line.strip().split('\t')
        repos[repoName] = repos[repoName].update(branch=repoBranch)
        branches.append(repoName)

    if set(branches) != set(repos.keys()):
        raise Exception('You must have all the same repos in branches that you do in repositories')

    try:
        for line in (l for l in open(os.path.join(configDir, 'checkouts')) if l.strip()):
            repos[line.strip()] = repos[line.strip()].update(exportType=CHECKOUT)
    except IOError:
        # File may not exist, ignore
        pass

    return repos

def main(options, args):
    logging.DEBUG = options('general.debug')
    
    if len(args) != 3:
        raise cli.MissingOptionError('Must specify PROJECT REPOPATH OUTPUTPATH, see --help')
    
    project, repoPath, outputPath = args

    if options('general.checkout') and options('general.export'):
        raise cli.InvalidOptionError('You cannot specify both checkout and export')
    
    logging.debugPrint(lambda : 'Loading repositories information...')
    repositories = loadRepositories(options('general.config_dir'))

    logging.debugPrint(lambda : 'Loaded repositories: %s' % (' '.join(repositories.keys()),))
    
    if project not in repositories:
        raise cli.InvalidOptionError('%s is not a valid project name' % project)

    repo = repositories[project]
    branch = options('general.branch') or repo.branch
    if not options('general.export') and (repo.exportType == CHECKOUT or options('general.checkout')):
        exportFunc = repo.rType.checkout
    else:
        exportFunc = repo.rType.export

    exportFunc(options, repo, repoPath, outputPath, branch)

if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS, usage='usage: %prog [options] PROJECT REPOPATH OUTPUTPATH\nDO NOT USE LEADING SLASHES FOR REPOPATH'))
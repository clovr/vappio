#!/usr/bin/env python
##
# Step 1 in cutting a release
# This runs on the build box

from igs.utils.cli import buildConfigN, notNone
from igs.utils.commands import runSystemEx

OPTIONS = [
    ('version_string', '', '--vs', 'Version string', notNone)
    ]


COMMANDS = [
    ##
    # Don't need this yet
    #"""shutdownNode.py""",
    """rm -rf /opt/db/*""",
    """apt-get clean""",
    """apt-get update""",
    """svn co https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/packages /opt/packages""",
    """dpkg --get-selections > /opt/packages/packages.latest""",
    """perl -e 'use ExtUtils::Installed;$inst = ExtUtils::Installed->new(); foreach my $mod ($inst->modules()){print "$mod ",$inst->version($mod),"\n"};' > /opt/packages/cpan.packages""",
    """svn commit /opt/packages -m "Updating package directory for release" """,
    """rm -rf /opt/packages""",
    """updateAllDirs.py --vappio-py""",
    """updateAllDirs.py""",
    """svn co https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/filesystem /opt/filesystem""",
    """find / -type f -or -type l -exec ls -l --time-style="+" {} \; | grep -v -E '(\/dev\/|\/proc\/|\/sys\/)' | sort > /opt/filesystem/filesystem.list""",
    """svn commit /opt/filesystem -m "Updating file system list" """,
    """rm -rf /opt/filesystem"""
    ]

def main(options, _args):
    open('/opt/CLOVR-RELEASE', 'w').write(options('general.version_string') + '\n')
    for c in COMMANDS:
        runSystemEx(c, log=True)


if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))    

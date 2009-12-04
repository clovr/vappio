#!/usr/bin/env python
##
# This updates every directory with the latest from SVN.
from igs.utils.commands import runSystemEx


def main(options):
    runSystemEx("""svn export --force https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/stow /usr/local/stow""")
    runSystemEx("""svn export --force https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/opt-packages /opt/opt-packages""")
    runSystemEx("""svn export --force https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/config_policies /opt/config_policies""")
    runSystemEx("""svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-py /opt/vappio-py""")
    runSystemEx("""svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-scripts /opt/vappio-scripts""")
    runSystemEx("""chmod +x /opt/vappio-py/vappio/cli/*.py""")


if __name__ == '__main__':
    ##
    # Just call it with None for now, will handle options later
    main(None)
    

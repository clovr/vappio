#!/usr/bin/env python
##
# This updates every directory with the latest from SVN.
import optparse

from igs.utils.cli import buildConfig
from igs.utils.commands import runSystemEx


def cliParser():
    parser = optparse.OptionParser()
    
    parser.add_option('', '--stow', dest='stow', action='store_true', help='Update Stow')
    parser.add_option('', '--opt-packages', dest='opt_packages', action='store_true', help='Update opt-packages')
    parser.add_option('', '--config_policies', dest='config_policies', action='store_true', help='Update config_policies')
    parser.add_option('', '--vappio-py', dest='vappio_py', action='store_true', help='Update vappio-py')
    parser.add_option('', '--vappio-scripts', dest='vappio_scripts', action='store_true', help='Update vappio-scripts')

    return parser


def cliMerger(cliOptions, _args):
    ##
    # If they are all false, set them all to true because they did not specify any
    if not (cliOptions.stow and
            cliOptions.opt_packages and
            cliOptions.config_policies and
            cliOptions_vappio_py and
            cliOptions.vappio_scripts):
        cliOptions.stow = True
        cliOptions.opt_packages = True
        cliOptions.config_policies = True
        cliOptions_vappio_py = True
        cliOptions.vappio_scripts = True
    
    return configFromMap({
        'stow': cliOptions.stow,
        'opt_packages': cliOptions.opt_packages,
        'config_policies': cliOptions.config_policies,
        'vappio_py': cliOptions.vappio_py,
        'vappio_scripts': cliOptions.vappio_scripts})
        


def main(options):
    if options('stow'):
        runSystemEx("""svn export --force https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/stow /usr/local/stow""")
    if options('opt_packages'):
        runSystemEx("""svn export --force https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/opt-packages /opt/opt-packages""")
    if options('config_policies'):
        runSystemEx("""svn export --force https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/config_policies /opt/config_policies""")
    if options('vappio_py'):
        runSystemEx("""svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-py /opt/vappio-py""")
        runSystemEx("""chmod +x /opt/vappio-py/vappio/cli/*.py""")
    if options('vappio_scripts'):
        runSystemEx("""svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-scripts /opt/vappio-scripts""")



if __name__ == '__main__':
    options = buildConfig(cliParser(), cliMerger)
    main(options)

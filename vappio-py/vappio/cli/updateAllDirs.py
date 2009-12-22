#!/usr/bin/env python
##
# This updates every directory with the latest from SVN.
from igs.utils.cli import buildConfigN, defaultIfNone
from igs.utils.commands import runSystemEx


OPTIONS = [
    ('stow', '', '--stow', 'Update stow', defaultIfNone(False), True),
    ('opt_packages', '', '--opt-packages', 'Update opt-packages', defaultIfNone(False), True),
    ('config_policies', '', '--config_policies', 'Update config_policies', defaultIfNone(False), True),
    ('vappio_py', '', '--vappio-py', 'Update vappio-py', defaultIfNone(False), True),
    ('vappio_scripts', '', '--vappio-scripts', 'Update vappio-scripts', defaultIfNone(False), True),
    ('clovr_pipelines', '', '--clovr_pipelines', 'Update clovr_pipelines', defaultIfNone(False), True),
    ('co', '', '--co', 'Check out rather than export', defaultIfNone(False), True),
    ]



def grabFromSVN(options, srcUrl, dstDir):
    cmd = ['svn']
    if options('general.co'):
        cmd += ['co']
    else:
        cmd += ['export', '--force']

    cmd += [srcUrl, dstDir]

    runSystemEx('rm -rf ' + dstDir, log=True)
    runSystemEx(' '.join(cmd), log=True)

def main(options, _args):
    updateAll = False
    for o in OPTIONS:
        if options('general.' + o[0]):
            break
    else:
        updateAll = True
        
    if options('general.stow') or updateAll:
        grabFromSVN(options, 'https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/stow', '/usr/local/stow')
    if options('general.opt_packages') or updateAll:
        grabFromSVN(options, 'https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/opt-packages', '/opt/opt-packages')
    if options('general.config_policies') or updateAll:
        grabFromSVN(options, 'https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/config_policies', '/opt/config_policies')
    if options('general.vappio_py') or updateAll:
        grabFromSVN(options, 'https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-py', '/opt/vappio-py')
        runSystemEx("""chmod +x /opt/vappio-py/vappio/cli/*.py""")
    if options('general.vappio_scripts') or updateAll:
        grabFromSVN(options, 'https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-scripts', '/opt/vappio-scripts')
        runSystemEx("""chmod -R +x /opt/vappio-scripts""")
        runSystemEx("""cp -f /opt/vappio-scripts/clovrEnv.sh /root""")
        runSystemEx("""cp -f /opt/vappio-scripts/local /etc/init.d/local""")
    if options('general.clovr_pipelines') or updateAll:
        grabFromSVN(options, 'https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/clovr_pipelines', '/opt/clovr_pipelines')


if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

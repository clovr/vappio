#!/usr/bin/env python
##
# This updates every directory with the latest from SVN.
from igs.utils.cli import buildConfigN, defaultIfNone
from igs.utils.commands import runSystemEx, runSingleProgramEx
from igs.utils.logging import errorPrint

OPTIONS = [
    ('stow', '', '--stow', 'Update stow', defaultIfNone(False), True),
    ('opt_packages', '', '--opt-packages', 'Update opt-packages', defaultIfNone(False), True),
    ('config_policies', '', '--config_policies', 'Update config_policies', defaultIfNone(False), True),
    ('vappio_py', '', '--vappio-py', 'Update vappio-py', defaultIfNone(False), True),
    ('vappio_scripts', '', '--vappio-scripts', 'Update vappio-scripts', defaultIfNone(False), True),
    ('clovr_pipelines', '', '--clovr_pipelines', 'Update clovr_pipelines', defaultIfNone(False), True),
    ('vappio_py_www', '', '--vappio-py-www', 'Update vappio-www/py-ww', defaultIfNone(False), True),
    ('vappio_conf', '', '--vappio-conf', 'Update vappio/conf', defaultIfNone(False), True),
    ('hudson', '', '--hudson', 'Update hudson', defaultIfNone(False), True),
    ('clovr_www', '', '--clovr-www', 'CloVR web gui', defaultIfNone(False), True),
    ('co', '', '--co', 'Check out rather than export', defaultIfNone(False), True),
    ]


class CheckoutModifiedError(Exception):
    pass

def grabFromSVN(options, srcUrl, dstDir):
    cmd = ['svn']
    if options('general.co'):
        cmd += ['co']
    else:
        cmd += ['export', '--force']

    cmd += [srcUrl, dstDir]

    outp = []
    runSingleProgramEx('svn status ' + dstDir, stdoutf=outp.append, stderrf=None, log=False)
    ##
    # If outp contains some output it means modifications have been made
    if outp:
        raise CheckoutModifiedError('There are modifications to %s, please commit them or revert them before continuing' % dstDir)
        

    
    runSystemEx('rm -rf ' + dstDir, log=True)
    runSystemEx(' '.join(cmd), log=True)

def main(options, _args):
    updateAll = False
    for o in OPTIONS:
        if options('general.' + o[0]):
            break
    else:
        updateAll = True


    try:
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
            runSystemEx("""chmod -R +x /opt/vappio-scripts""", log=True)
            runSystemEx("""cp -f /opt/vappio-scripts/clovrEnv.sh /root""", log=True)
            runSystemEx("""cp -f /opt/vappio-scripts/local /etc/init.d/local""", log=True)
            runSystemEx("""cp -f /opt/vappio-scripts/rc.local /etc/init.d/rc.local""", log=True)
            runSystemEx("""cp -f /opt/vappio-scripts/screenrc /root/.screenrc""", log=True)
        if options('general.clovr_pipelines') or updateAll:
            grabFromSVN(options, 'https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/clovr_pipelines', '/opt/clovr_pipelines')
        if options('general.vappio_py_www') or updateAll:
            grabFromSVN(options, 'https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-www/py-www', '/var/www/vappio')
        ##    
        # Only want to do this one when specified
        if options('general.vappio_conf'):
            grabFromSVN(options, 'https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-conf', '/opt/vappio-conf')

        if options('general.hudson') or updateAll:
            grabFromSVN(options, 'https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/hudson/hudson-config/jobs', '/var/lib/hudson/jobs')
            grabFromSVN(options, 'https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/hudson/hudson-scripts', '/opt/hudson')
            runSystemEx("""chown -R hudson.nogroup /var/lib/hudson/jobs""", log=True)

        if options('general.clovr_www') or updateAll:
            grabFromSVN(options, 'https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/clovr-www', '/var/www/clovr')
            
    except CheckoutModifiedError, err:
        errorPrint(str(err))

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

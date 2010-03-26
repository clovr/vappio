#!/usr/bin/env python
##
# This provides information on the status of the VM.
# Provided informatino:
#
# - Are shared dirs enabled
# - Is networking enabled
# - What clusters are running

from igs.utils.cli import buildConfigN, notNone, restrictValues, defaultIfNone
from igs.utils.functional import identity
from igs.utils.logging import debugPrint, errorPrint, logPrint
from igs.utils.commands import runSystemEx, runSingleProgramEx

from vappio.webservice.cluster import listClusters, loadCluster

from vappio.ec2.control import listInstances

OPTIONS = [
    ('one_line', '-1', '--one-line', 'Give a condenced version of output in one line', identity, True),
    ]


def sharedFoldersEnabled():
    try:
        ##
        # Are we running VMWare?
        runSystemEx('vmware-checkvm > /dev/null 2>&1')

        res = []
        runSingleProgramEx('df', res.append, None)
        return [l for l in res if l.startswith('.host:/shared')]
    except:
        ##
        # If we aren't running VMWare, just assume it worked for now
        return True

def networkingEnabled():
    res = []
    runSingleProgramEx('ifconfig', res.append, None)
    return [l for l in res if 'inet addr:' in l and '127.0.0.1' not in l]

def getNumberOfInstances():
    return 'Unknown'
    # try:
    #     return str(len(listInstances()))
    # except:
    #     return 'Unknown'

def main(options, _args):
    state = {
        'shared': sharedFoldersEnabled(),
        'clusters': listClusters('localhost'),
        'networking': networkingEnabled()
        }

    if options('general.one_line'):
        line = []
        if not state['shared']:
            line.append('Shared Folders Are Not Enabled, Please Enable Them And Restart!')

        if not state['networking']:
            line.append('Networking Is Not Enabled, Please Restart!')

        if not line:
             line.append('Instances: %s' % getNumberOfInstances())
             line.append('Clusters: ' + ' '.join(state['clusters']))

        print ' :: '.join(line)
    else:
        if not state['shared']:
            print '*'*40
            print 'Shared folders are not enabled.  These need to be enabled for CloVR to work properly.'
            print 'Please enable shared folders and restart CloVR.'

        if not state['networking']:
            print '+'*40
            print 'It does not appear that networking has come up properly.  Networking is required for ClOVR to work properly'
            print 'Try to restart CloVR to see if networking comes up properly.  If that does not work please consult your help desk.'


if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

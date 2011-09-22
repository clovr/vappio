# Commands:
# Update - qconf -rattr queue slots "[$HOSTNAME=$SLOTS]" $QUEUE

import StringIO

from twisted.internet import defer

from igs_tx.utils import commands

def _parseSGEConf(data):
    lines = data.split('\n')

    multiline = False
    ret = {}
    
    for line in lines:
        line = line.strip()

        if line:
            if not multiline:
                key, value = line.split(' ', 1)
                value = value.strip().rstrip('\\')
                ret[key] = value
            else:
                # Making use of the fact that the key was created
                # in the previous iteration and is stil lin scope
                ret[key] += line

            multiline = (line[-1] == '\\')

    return ret
            

@defer.inlineCallbacks
def listSlotsForQueue(queue):
    output = yield commands.getOutput(['qconf', '-sq', queue])

    conf = _parseSGEConf(output)
    slots = conf['slots'].split(',')

    clusterWide = [s for s in slots if s[0] != '[']
    nodeSpecific = [s[1:-1].split('=') for s in slots if s[0] == '[']

    defer.returnValue({'cluster': int(clusterWide),
                       'nodes': dict([(h, int(v)) for h, v in nodeSpecific])})

def setSlotsForQueue(queue, hostname, slots):
    return commands.runProcess(['qconf',
                                '-rattr',
                                'queue',
                                'slots',
                                '[%s=%d]' % (hostname, slots),
                                queue],
                               log=True)

##
# These are various tools useful for blast pipelines
import itertools

from igs.utils.config import replaceStr

def commonPrefix(s1, s2):
    """Finds the common prefix between two iterables"""
    return s1[:len(list(itertools.takewhile(lambda (x, y) : x == y, zip(s1, s2))))]

    
def tagToRefDBPath(tagFname):
    def _(conf):
        files = open(replaceStr(tagFname, conf)).readlines()
        prefix = files.pop(0)
        for f in files:
            prefix = commonPrefix(prefix, f)

        if prefix[-1] == '.':
            prefix = prefix[:-1]
        elif prefix.endswith('.n') or prefix.endswith('.p'):
            prefix = prefix[:-2]

        return prefix

    return _


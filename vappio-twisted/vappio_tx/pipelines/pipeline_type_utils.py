# Various utilities to make it easier to do things with pipeline types
import itertools

from igs.utils import config

def commonPrefix(s1, s2):
    """Finds the common prefix between two iterables"""
    return s1[:len(list(itertools.takewhile(lambda (x, y) : x == y, zip(s1, s2))))]

    
def tagToRefDBPath(tagFname):
    files = open(tagFname).readlines()
    prefix = files.pop(0)
    for f in files:
        prefix = commonPrefix(prefix, f)

    if prefix[-1] == '.':
        prefix = prefix[:-1]
    elif prefix.endswith('.n') or prefix.endswith('.p'):
        prefix = prefix[:-2]

    return prefix


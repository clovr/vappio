##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath

##
# Need to know where the template lives
TEMPLATE_NAME = 'wait_tmpl'

def fullPathOrTag(x):
    if x[0] == '/':
        return x
    else:
        return tagToRefDBPath(x)

OPTIONS = [
    ('TIME', '', '--TIME', 'Time to sleep', defaultIfNone('1'))
    ('INPUT_FILE', '', '--INPUT_FILE', 'One or more input files', defaultIfNone('/mnt/staging'))
    ]


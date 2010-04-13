##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath

##
# Need to know where the template lives
TEMPLATE_NAME = 'blastall_tmpl'

def fullPathOrTag(x):
    if x[0] == '/':
        return x
    else:
        return tagToRefDBPath(x)

OPTIONS = [
    ('INPUT_FILE_LIST', '', '--INPUT_FILE_LIST', 'The input file list of sequences', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('REF_DB_PATH', '', '--REF_DB_PATH', 'The reference db for the blast run', compose(tagToRefDBPath, lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ##
    # For SEQS_PER_FILE the function at the end may seem odd, but really this is just validating that they give us an int
    # we actually want it as a string in order to do the replacement in the config file, which is why we do
    # str . int
    ('SEQS_PER_FILE', '', '--SEQS_PER_FILE', 'Number of sequences per file, defaults to 1000', compose(str, int, defaultIfNone('1000'))),
    ('OTHER_OPTS', '', '--OTHER_OPTS', 'Other options to pass to blast', defaultIfNone('')),
    ]


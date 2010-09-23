##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues, composeCLI, notBlank

from vappio.pipeline_tools.blast import tagToRefDBPath

##
# Need to know where the template lives
TEMPLATE_NAME = 'blastall'

OPTIONS = [
    ('input.INPUT_FILE_LIST', '', '--INPUT_FILE_LIST', 'The input tag of sequences', composeCLI(lambda x : os.path.join('${dirs.tag_dir}', x), notBlank, defaultIfNone('${input.INPUT_TAG}'))),
    ('input.REF_DB_PATH', '', '--REF_DB_TAG', 'The reference db for the blast run',
     composeCLI(tagToRefDBPath, lambda x : os.path.join('${dirs.tag_dir}/', x), notBlank, defaultIfNone('${input.REF_DB_TAG}'))),
    ('misc.PROGRAM', '', '--PROGRAM', 'The blast program to run (blastp, blastx, ..)', restrictValues(['blastn', 'blastp', 'blastx', 'tblastn', 'tblastx'])),
    ('misc.EXPECT', '', '--EXPECT', 'e-value cutoff, default is 1e-5', notNone),
    ##
    # For SEQS_PER_FILE the function at the end may seem odd, but really this is just validating that they give us an int
    # we actually want it as a string in order to do the replacement in the config file, which is why we do
    # str . int
    ('misc.SEQS_PER_FILE', '', '--SEQS_PER_FILE', 'Number of sequences per file, defaults to 1000', compose(str, int, defaultIfNone('1000'))),
    ('misc.OTHER_OPTS', '', '--OTHER_OPTS', 'Other options to pass to blast', defaultIfNone('')),
    ]


##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues, composeCLI, notBlank

from vappio.pipeline_tools.blast import tagToRefDBPath

def decideWordLength(blastProgramOrWordSize):
    try:
        return int(blastProgramOrWordSize)
    except ValueError:
        if blastProgram == 'blastn':
            return 11
        elif blastProgram == 'megablast':
            return 28
        else:
            return 3

#
# Need to know where the template lives
TEMPLATE_NAME = 'clovr_search_webfrontend'

OPTIONS = [
    ('input.INPUT_FILE_LIST', '', '--INPUT_FILE_LIST', 'The input tag of sequences', composeCLI(lambda x : os.path.join('${dirs.tag_dir}', x), notBlank, defaultIfNone('${input.INPUT_TAG}'))),
    ('input.REF_DB_PATH', '', '--REF_DB_TAG', 'The reference db for the blast run',
     composeCLI(tagToRefDBPath, lambda x : os.path.join('${dirs.tag_dir}/', x), notBlank, defaultIfNone('${input.REF_DB_TAG}'))),
    ('params.PROGRAM', '', '--PROGRAM', 'The blast program to run (blastp, blastx, ..)', restrictValues(['blastn', 'blastp', 'blastx', 'tblastn', 'tblastx'])),
    ('params.EXPECT', '', '--EXPECT', 'e-value cutoff, default is 1e-5', defaultIfNone('1e-5')),
    ('params.MAX_TARGET_SEQ', '', '--MAX_TARGET_SEQ', 'Number of database sequence to show alignments for', compose(lambda x: '-b ' + str(x), int, defaultIfNone('250'))),
    ('params.WORD_SIZE', '', '--WORD_SIZE', 'Word size', composeCLI(lambda x: '-W ' + str(x), int, decideWordLength, defaultIfNone('${params.PROGRAM}'))),
    ('params.LOW_COMPLEXITY', '', '--LOW_COMPLEXITY', 'Low complexity filter', compose(lambda x: '-F ' + (x == 'Yes' and 'T' or 'F'), restrictValues(['Yes', 'No']), defaultIfNone('No'))),
    ('params.OTHER_OPTS', '', '--OTHER_OPTS', 'Other options to pass to blast', defaultIfNone('')),
    ]


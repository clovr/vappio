##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

##
# Need to know where the template lives
TEMPLATE_NAME = 'clovr_assembly_celera'

OPTIONS = [
    ('INPUT_FILE_LIST', '', '--INPUT_FILE_LIST', 'The input file list of sequences', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('OUTPUT_PREFIX', '', '--OUTPUT_PREFIX', 'Used in ID generation, Locus Tags, etc.', notNone),
    ('CLEAR', '', '--CLEAR', 'Can be either all, 454, none, n, pair-of-n, or discard-n', compose(restrictValues(['all', '454', 'none', 'n', 'pair-of-n', 'discard-n']), defaultIfNone('discard-n'))),
    ('TRIM', '', '--TRIM', 'Can be either none, soft, hard, chop', compose(restrictValues(['none', 'soft', 'hard', 'chop']), defaultIfNone('none'))),
    ('LINKER', '', '--LINKER', 'If the 454 run was paired end, the linker type used (either titanium or flx. See sffToCA documentation for specific linker sequences for these two defaults). This could also be the sequence of the linker itself.', defaultIfNone('')),
    ('INSERT_SIZE', '', '--INSERT_SIZE', 'Only needed if --LINKER option is specified. Mates are on average i +- d bp apart (i.e. --INSERT_SIZE "8000 1000").', defaultIfNone('')),
    ('SPEC_FILE', '', '--SPEC_FILE', 'Spec file for celera assembler run', defaultIfNone('/dev/null')),
    ('GROUP_COUNT', '', '--GROUP_COUNT', 'Corresponds to number of groups to split data into (Ergatis)', defaultIfNone('50')),
    ('SKIP_BANK', '', '--SKIP_BANK', 'Skip conversion of celera assembler output to AMOS bank format.', compose(lambda x : x and "toAmos,bank-transact,cleanup afg file" or "null", defaultIfNone(False)))
    ]

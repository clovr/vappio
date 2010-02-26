##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

##
# Need to know where the template lives
TEMPLATE_NAME = 'barebones_prok'


OPTIONS = [
    ('INPUT_FILE_LIST', '', '--INPUT_FILE_LIST', 'The input file list of sequences', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('OUTPUT_PREFIX', '', '--OUTPUT_PREFIX', 'Used in ID generation, Locus Tags, etc.', notNone),
    ('CLEAR', '', '--CLEAR', 'Can be either all, 454, none, n, pair-of-n, or discard-n', compose(restrictValues(['all', '454', 'none', 'n', 'pair-of-n', 'discard-n']), defaultIfNone('discard-n'))),
    ('TRIM', '', '--TRIM', 'Can be either none, soft, hard, chop', compose(restrictValues(['none', 'soft', 'hard', 'chop']), defaultIfNone('none'))),
    ('SPEC_FILE', '', '--SPEC_FILE', 'Spec file for celera assembler run', defaultIfNone('/dev/null')),
    ('ORGANISM', '', '--ORGANISM', 'Organism name', defaultIfNone('/dev/null')),
    ('GROUP_COUNT', '', '--GROUP_COUNT', 'Corresponds to number of groups to split data into (Ergatis)', defaultIfNone('50')),
    ('DATABASE_PATH', '', '--DATABASE_PATH', 'The tag for the uploaded reference database set', compose(lambda x : '${dirs.upload_dir}/' + x, notNone))
    ]


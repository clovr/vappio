##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

##
# Need to know where the template lives
TEMPLATE_NAME = 'clovr_microbe_annotation'

OPTIONS = [
    ('input.INPUT_FILE_LIST', '', '--INPUT_FILE_LIST', 'The input file list of sequences', compose(lambda x : '${dirs.tag_dir}/' + x, defaultIfNone('${input.INPUT_FSA_TAG}'))),
    ('input.OUTPUT_PREFIX', '', '--OUTPUT_PREFIX', 'Used in ID generation, Locus Tags, etc.', notNone),
    ('input.ORGANISM', '', '--ORGANISM', 'Organism name', defaultIfNone('/dev/null')),
    ('input.GROUP_COUNT', '', '--GROUP_COUNT', 'Corresponds to number of groups to split data into (Ergatis)', defaultIfNone('50')),
    ('input.DATABASE_PATH', '', '--DATABASE_PATH', 'The tag for the uploaded reference database set', compose(lambda x : '${dirs.upload_dir}/' + x, defaultIfNone('${input.REFERENCE_DB_TAG}'))),
    ]


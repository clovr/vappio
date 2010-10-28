##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os
import re

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

##
# Need to know where the template lives
TEMPLATE_NAME = 'clovr_microbe_illumina'


OPTIONS = [
    ('input.SHORT_PAIRED_LIST', '', '--SHORT_PAIRED_LIST', 'A comma separated list of input tags. Each tag should contain two files.', compose( lambda x : ','.join(['${dirs.tag_dir}/' + y for y in x and re.split('[\s,]+', x) or []]), defaultIfNone('${input.SHORT_PAIRED_FILES}'))),
    ('input.LONG_PAIRED_LIST', '', '--LONG_PAIRED_LIST', 'A common separated list of input tags. Each tag should contain two files', compose( lambda x : ','.join(['${dirs.tag_dir}/' + y for y in x and re.split('[\s,]+', x) or []]), defaultIfNone('${input.LONG_PAIRED_FILES}') ) ),
    ('input.SHORT_INPUT_LIST', '', '--SHORT_INPUT_LIST', 'Input tag for non paired end short read data.', compose( lambda x : ','.join(['${dirs.tag_dir}/' + y for y in x.split()]), defaultIfNone('${input.SHORT_FILES}')) ),
    ('input.LONG_INPUT_LIST', '', '--LONG_INPUT_LIST', 'Input tag for non paired long read data', compose( lambda x : ','.join(['${dirs.tag_dir}/' + y for y in x.split()]), defaultIfNone('${input.LONG_FILES}')) ),
    ('input.OUTPUT_PREFIX', '', '--OUTPUT_PREFIX', 'Used in ID generation, Locus Tags, etc.', notNone),
    ('input.START_HASH_LENGTH', '', '--START_HASH_LENGTH', 'Starting hash size: default 19. Must be Odd.', defaultIfNone('19')),
    ('input.END_HASH_LENGTH', '', '--END_HASH_LENGTH', 'Ending hash size: default 31. Must be Odd.', defaultIfNone('31')),
    ('input.VELVETG_OPTS', '', '--VELVETG_OPTS', 'Options that will be passed onto velvetg. If using paired end reads, use at least -ins_length and -ins_length_sd. -min_contig_lgth is already set.', defaultIfNone('')),
    ('input.ORGANISM', '', '--ORGANISM', 'Organism name', defaultIfNone('/dev/null')),
    ('input.GROUP_COUNT', '', '--GROUP_COUNT', 'Corresponds to number of groups to split data into (Ergatis)', defaultIfNone('50')),
    ('input.DATABASE_PATH', '', '--DATABASE_PATH', 'The tag for the uploaded reference database set', compose(lambda x : '${dirs.upload_dir}/' + x, defaultIfNone('${input.REFERENCE_DB_TAG}'))),
    ]


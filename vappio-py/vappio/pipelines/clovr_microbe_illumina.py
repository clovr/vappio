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
    ('SHORT_PAIRED_LIST', '', '--SHORT_PAIRED_LIST', 'A comma separated list of input tags. Each tag should contain two files.', compose( lambda x : ','.join(['${dirs.tag_dir}/' + y for y in x and re.split('[\s,]+', x) or []]), defaultIfNone(''))),
    ('LONG_PAIRED_LIST', '', '--LONG_PAIRED_LIST', 'A common separated list of input tags. Each tag should contain two files', compose( lambda x : ','.join(['${dirs.tag_dir}/' + y for y in x and re.split('[\s,]+', x) or []]), defaultIfNone('') ) ),
    ('SHORT_INPUT_LIST', '', '--SHORT_INPUT_LIST', 'Input tag for non paired end short read data.', compose( lambda x : ','.join(['${dirs.tag_dir}/' + y for y in x.split()]), defaultIfNone('')) ),
    ('LONG_INPUT_LIST', '', '--LONG_INPUT_LIST', 'Input tag for non paired long read data', compose( lambda x : ','.join(['${dirs.tag_dir}/' + y for y in x.split()]), defaultIfNone('')) ),
    ('OUTPUT_PREFIX', '', '--OUTPUT_PREFIX', 'Used in ID generation, Locus Tags, etc.', notNone),
    ('START_HASH_LENGTH', '', '--START_HASH_LENGTH', 'Starting hash size: default 19. Must be Odd.', defaultIfNone('19')),
    ('END_HASH_LENGTH', '', '--END_HASH_LENGTH', 'Ending hash size: default 31. Must be Odd.', defaultIfNone('31')),
    ('VELVETG_OPTS', '', '--VELVETG_OPTS', 'Options that will be passed onto velvetg. If using paired end reads, use at least -ins_length and -ins_length_sd. -min_contig_lgth is already set.', defaultIfNone('')),
    ('ORGANISM', '', '--ORGANISM', 'Organism name', defaultIfNone('/dev/null')),
    ('GROUP_COUNT', '', '--GROUP_COUNT', 'Corresponds to number of groups to split data into (Ergatis)', defaultIfNone('50')),
    ('DATABASE_PATH', '', '--DATABASE_PATH', 'The tag for the uploaded reference database set', compose(lambda x : '${dirs.upload_dir}/' + x, notNone)),
    ]


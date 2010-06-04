##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

##
# Need to know where the template lives
TEMPLATE_NAME = 'illumina_prok_annot'


OPTIONS = [
    ('INPUT_FILE', '', '--INPUT_FILE', 'The input file list of sequences', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('OUTPUT_PREFIX', '', '--OUTPUT_PREFIX', 'Used in ID generation, Locus Tags, etc.', notNone),
    ('FILE_FORMAT', '', '--FILE_FORMAT', 'Can be any of the following: fasta, fastq, fasta.gz, fastq.gz, eland, gerald', compose(restrictValues(['fasta', 'fastq', 'fasta.gz', 'fastq.gz', 'eland', 'gerald']), notNone)),
    ('READ_TYPE', '', '--READ_TYPE', 'Can be either short, shortPaired, long, longPaired', compose(restrictValues(['short', 'shortPaired', 'long', 'longPaired']), notNone)),
    ('START_HASH_LENGTH', '', '--START_HASH_LENGTH', 'Starting hash size: default 19. Must be Odd.', defaultIfNone('19')),
    ('END_HASH_LENGTH', '', '--END_HASH_LENGTH', 'Ending hash size: default 31. Must be Odd.', defaultIfNone('31')),
    ('VELVETG_OPTS', '', '--VELVETG_OPTS', 'Options that will be passed onto velvetg. If using paired end reads, use at least -ins_length and -ins_length_sd. -min_contig_lgth is already set.', defaultIfNone(''))
    ]


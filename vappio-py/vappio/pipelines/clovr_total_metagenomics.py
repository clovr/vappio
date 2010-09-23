##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath

##
# Need to know where the template lives
TEMPLATE_NAME = 'clovr_total_metagenomics'


OPTIONS = [
    ('input.INPUT_FILE_LIST', '', '--INPUT_FILE_LIST', 'The input file list of SFF files', compose(lambda x : '${dirs.tag_dir}/' + x, defaultIfNone('${input.INPUT_TAG}'))),
    ('input.DB_TAG', '', '--DB_TAG', 'The root database path', compose(tagToRefDBPath, lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('params.SEQS_PER_FILE', '', '--SEQS_PER_FILE', 'Number of sequences per file produced by split_multifasta', defaultIfNone("")),
    ('params.CUTOFF', '', '--CUTOFF', 'Metagene gene calls below this nucleotide length are discarded', defaultIfNone("")),
    ('params.TOTAL_FILES','', '--TOTAL_FILES', 'Tell split_multifasta to produce exactly this amount of files', defaultIfNone("")),
    ('params.NUM_SEQS', '', '--NUM_SEQS', 'Number of sequences per bsml file produced by metagene', defaultIfNone("150")),
    ('params.GROUP_COUNT', '', '--GROUP_COUNT', 'Group count to use in Ergatis', defaultIfNone("50"))
    ]

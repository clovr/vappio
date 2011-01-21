##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath

TEMPLATE_NAME = 'clovr_mapping_bowtie_indices'

OPTIONS = [
    ('input.REFERENCE_TAG', '', '--REFERENCE_TAG', 'The input file list of bowtie-build produce indices', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('input.INPUT_READS_TAG', '', '--INPUT_READS_TAG', 'The input file list of a single unpaired or set of paired reads', notNone),
    ('params.MAX_INSERT_SIZE', '', '--MAX_INSERT_SIZE', 'Bowtie maximum insert size', defaultIfNone("300")),
    ('params.MAX_MISMATCHES', '', '--MAX_MISMATCHES', 'Bowtie maximum number of mismatches', defaultIfNone("2")),
    ('params.MAX_ALIGNS_PER_READ', '', '--MAX_ALIGNS_PER_READ', 'Bowtie maximum number of alignments per read.', defaultIfNone("1")),
    ('params.BOWTIE_OPTS', '', '--BOWTIE_OPTS', 'Any other bowtie command-line arguments', defaultIfNone(""))
    ]

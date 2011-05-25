##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

##
# Need to know where the template lives
TEMPLATE_NAME = 'clovr_rna_seq_pileup'

OPTIONS = [
    ('input.INPUT_SAM_TAG', '', '--INPUT_SAM_TAG', 'The input file list of SAM files', compose(lambda x : '${dirs.tag_dir}/' + x, defaultIfNone('${input.INPUT_SAM_TAG}'))),
    ('input.REFERENCE_TAG', '', '--REFERENCE_TAG', 'The reference FASTA file', compose(lambda x : '${dirs.tag_dir}/' + x, defaultIfNone('${input.REFERENCE_TAG}')))
    ]

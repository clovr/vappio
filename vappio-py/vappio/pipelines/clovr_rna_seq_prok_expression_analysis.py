##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

##
# Need to know where the template lives
TEMPLATE_NAME = 'clovr_rna_seq_prok_expression_analysis'

OPTIONS = [
    ('input.INPUT_SAM_TAG', '', '--INPUT_SAM_TAG', 'The input file list of SAM files', compose(lambda x : '${dirs.tag_dir}/' + x, defaultIfNone('${input.INPUT_SAM_TAG}'))),
    ('input.INPUT_GFF3_TAG', '', '--REFERENCE_TAG', 'GFF3 file containing reference sequence and annotations', compose(lambda x : '${dirs.tag_dir}/' + x, defaultIfNone('${input.INPUT_GFF3_TAG}'))),
    ('input.INPUT_SAMPLE_MAP_TAG', '', '--INPUT_SAMPLE_MAP_TAG', 'Tab-delimeted file usedd to map the read count files to the appropriate phenotype and replicate.', compose(lambda x : '${dirs.tag_dir}/' + x, defaultIfNone('${input.INPUT_SAMPLE_MAP_TAG}'))),
    ('params.COUNT_MODE', '', '--COUNT_MODE', 'Scheme to decipher overlapping features and reads', compose(restrictValues(['union', 'intersection-strict', 'intersection-nonempty']), defaultIfNone("union"))),
    ('params.COUNTING_FEATURE', '', '--COUNTING_FEATURE', 'Feature type to extract from gtf file and count over', notNone),
    ('params.MIN_ALIGN_QUAL', '', '--MIN_ALIGN_QUAL', 'Minimum quality of alignment required to count a read', defaultIfNone(0)),
    ('params.IS_STRANDED', '', '--IS_STRANDED', 'Minimum quality of alignment required to count a read', compose(restrictValues(['yes', 'no']), defaultIfNone('no'))),
    ('params.ID_ATTRIBUTE', '', '--ID_ATTRIBUTE', 'Attribute upon which to group features on when counting reads', notNone)
    ]

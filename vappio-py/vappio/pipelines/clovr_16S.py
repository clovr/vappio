##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath

##
# Need to know where the template lives
TEMPLATE_NAME = 'clovr_16S'

OPTIONS = [
    ('input.FASTA_FILE_LIST', '', '--FASTA_TAG', 'The input file list of FASTA files', compose(lambda x : '${dirs.tag_dir}/' + x, defaultIfNone('${input.FASTA_TAG}'))),
    ('input.MAPPING_FILE_LIST', '', '--MAPPING_TAG', 'Mapping data file', compose(lambda x : '${dirs.tag_dir}/' + x, defaultIfNone('${input.MAPPING_TAG}'))),
    ('params.GROUP_COUNT', '', '--GROUP_COUNT', 'Ergatis group count', defaultIfNone("50"))
    ]

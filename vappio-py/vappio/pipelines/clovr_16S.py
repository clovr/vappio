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
    ('input.FASTA_TAG', '', '--FASTA_TAG', 'The input file list of FASTA files', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('input.MAPPING_TAG', '', '--MAPPING_TAG', 'Mapping data file', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('input.DB_TAG', '', '--DB_TAG', 'The root database path', compose(lambda x : '${dirs.upload_dir}/' + x, notNone)),
    ('params.GROUP_COUNT', '', '--GROUP_COUNT', 'Ergatis group count', defaultIfNone("50"))
    ]

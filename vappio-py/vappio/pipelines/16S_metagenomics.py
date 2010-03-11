##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath

##
# Need to know where the template lives
TEMPLATE_NAME = '16S_metagenomics'


OPTIONS = [
    ('INPUT_FILE_LIST', '', '--INPUT_FILE_LIST', 'The input file list of FASTA files', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('DB_PATH', '', '--DB_PATH', 'The root database path', compose(lambda x : '${dirs.upload_dir}/' + x, notNone)),
    ('GROUP_COUNT', '', '--GROUP_COUNT', 'Ergatis group count', defaultIfNone("50"))
    ]

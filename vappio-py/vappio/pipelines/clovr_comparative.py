TEMPLATE_NAME = 'clovr_comparative'
##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath
TEMPLATE_NAME = 'clovr_comparative'

OPTIONS = [('input.INPUT_FILE_LIST', '', '--INPUT_FILE_LIST', 'The input file list of sequences', compose(lambda x : '${dirs.tag_dir}/' + x, defaultIfNone('${input.GENBANK_TAG}')))]


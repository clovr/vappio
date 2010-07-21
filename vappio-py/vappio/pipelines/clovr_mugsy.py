TEMPLATE_NAME = 'clovr_mugsy'
##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath
TEMPLATE_NAME = 'clovr_mugsy'

OPTIONS = [('BSML_FILE_LIST', '', '--BSML_FILE_LIST', 'The list of bsml files', compose(lambda x : '${dirs.tag_dir}/' + x, notNone))]


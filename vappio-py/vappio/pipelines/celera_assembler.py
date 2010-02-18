##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath

##
# Need to know where the template lives
TEMPLATE_NAME = 'celera_assembler'


OPTIONS = [
    ('INPUT_FILE_LIST', '', '--INPUT_FILE_LIST', 'The input file list of SFF files', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('SPEC_FILE', '', '--SPEC_FILE', 'Spec file containing celera-assembler configuration options.', notNone)
    ]


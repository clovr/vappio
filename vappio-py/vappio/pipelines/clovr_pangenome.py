TEMPLATE_NAME = 'clovr_pangenome'
##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath
TEMPLATE_NAME = 'clovr_pangenome'

OPTIONS = [('input.GENBANK_TAG', '', '--GENBANK_TAG', 'The input file list of GENBANK files', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)),
           ('input.MAP_TAG', '', '--MAP_TAG', 'The input file list of MAPPING files', compose(lambda x : '${dirs.tag_dir}/' + x, notNone))]

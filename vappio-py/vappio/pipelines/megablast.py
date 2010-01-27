##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath

from vappio.pipelines import blastn

##
# Need to know where the template lives
TEMPLATE_NAME = 'megablast_tmpl'

OPTIONS = blastn.OPTIONS


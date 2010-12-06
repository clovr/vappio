##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath

TEMPLATE_NAME = 'clovr_mapping_crossbow'

OPTIONS = [
    ('input.REFERENCE_JAR_TAG', '', '--REFERENCE_JAR_TAG', 'The input file list of crossbow compliant reference jars', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('input.INPUT_MANIFEST_TAG', '', '--INPUT_MANIFEST_TAG', 'The input file list of manifest files', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('param.OUTPUT_PREFIX', '', '--OUTPUT_PREFIX', 'Output prefix that will be used to name all output files', notNone),
    ('param.CROSSBOW_OPTS', '', '--CROSSBOW_OPTS', 'Any crossbow command-line arguments', defaultIfNone(""))
    ]

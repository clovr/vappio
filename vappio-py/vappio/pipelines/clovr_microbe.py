
##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

##
# Need to know where the template lives
TEMPLATE_NAME = 'clovr_microbe'


OPTIONS = [
    ('VAPPIO_CLI','', '--VAPPIO_CLI', '', defaultIfNone('/opt/vappio-py/vappio/cli/')),
    ('CLUSTER_TAG', '', '--CLUSTER_TAG', '', defaultIfNone('local')),
    ('PIPELINE_NAME', '', '--PIPELINE_NAME', '', defaultIfNone('noname_pipeline')),
    ('PIPELINE_TEMPLATE','', '--PIPELINE_TEMPLATE', '', identity),
    ('OUTPUT_DIRECTORY','', '--OUTPUT_DIRECTORY', '', identity),
    ('TEMPLATE_DIR','', '--TEMPLATE_DIR', '', identity),
    ('POSTRUN_TEMPLATE_XML','', '--POSTRUN_TEMPLATE_XML', '', defaultIfNone('noop.xml')),
    ('PRERUN_TEMPLATE_XML','', '--PRERUN_TEMPLATE_XML', '', defaultIfNone('noop.xml')),
    ('PRESTART_TEMPLATE_XML','', '--PRESTART_TEMPLATE_XML', '', defaultIfNone('noop.xml'))
    ]



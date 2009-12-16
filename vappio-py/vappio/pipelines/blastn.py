##
# This handles running a blastn pipeline
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import id


##
# Need to know where the template lives
TEMPLATE_DIR = '/opt/clovr_pipelines/workflow/project_saved_templates/blastn_tmpl'


##
# These are options that will be taken from the command line.  The
# format is (name, func, description)
#
# Where
# name - the name they will pass on the command line, this also matches the name of the variable in
#        the config file
# func - A functiont hat is applied to the option from the command line, if nothing needs to be
#        done simply use igs.utils.functional.id
# description - Just a brief description of the variable, this will be in the --help for the pipeline
OPTIONS = [
    ('INPUT_FILE_LIST', id, 'The input file list of sequences'),
    ('REF_DB_PATH', id, 'The reference db for the blast run')
    ]


##
# This handles running a blastn pipeline
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, combose
from igs.utils.cli import notNone, defaultIfNone



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
    ('INPUT_FILE_LIST', '', '--INPUT_FILE_LIST', 'The input file list of sequences', compose(lambda x : '${dirs.upload_dir}/tags/' + x, notNone)),
    ('REF_DB_PATH', '', '--REF_DB_PATH', 'The reference db for the blast run', compose(lambda x : '${dirs.upload_dir}/' + x), notNone)),
    ##
    # For SEQS_PER_FILE the function at the end may seem odd, but really this is just validating that they give us an int
    # we actually want it as a string in order to do the replacement in the config file, which is why we do
    # str . int
    ('SEQS_PER_FILE', '', '--SEQS_PER_FILE', 'Number of sequences per file, defaults to 1000', compose(str, int, defaultIfNone('1000'))),
    ]



##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

##
# Need to know where the template lives
TEMPLATE_DIR = '/opt/clovr_pipelines/workflow/project_saved_templates/total_metagenomics'


OPTIONS = [
    ('INPUT_FILE_LIST', '', '--INPUT_FILE_LIST', 'The input file list of sequences', compose(lambda x : '${dirs.upload_dir}/tags/' + x, notNone)),
    ('BLASTN_DB_PATH', '', '--BLASTN_DB_PATH', 'The reference db for the blast run', compose(lambda x : '${dirs.upload_dir}/' + x, notNone)),
    ('BLASTP_DB_PATH', '', '--BLASTP_DB_PATH', 'The reference db for the blast run', compose(lambda x : '${dirs.upload_dir}/' + x, notNone)),
    ##
    # For SEQS_PER_FILE the function at the end may seem odd, but really this is just validating that they give us an int
    # we actually want it as a string in order to do the replacement in the config file, which is why we do
    # str . int
    #('SEQS_PER_FILE', '', '--SEQS_PER_FILE', 'Number of sequences per file, defaults to 1000', compose(str, int, defaultIfNone('1000'))),
    ('LIBRARY', '', '--LIBRARY', 'e-value cutoff, default is 1e-5', defaultIfNone('1e-5')),
    ('TRIM', '', '--TRIM', 'Other options to pass to blast', defaultIfNone('')),
    ('CLEAR', '', '--CLEAR', 'Filter query, default is T', notNone), 
    ('SPEC_FILE', '', '--SPEC_FILE', 'Filter query, default is T', notNone)
    ]


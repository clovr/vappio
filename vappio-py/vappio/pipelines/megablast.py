##
# This handles running a blastn pipeline
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone



def restrictValues(values):
    def _(v):
        if v not in values:
            raise Exception('Value must be one of: %s' % ', '.join([str(x) for x in values]))
        return v

    return _

##
# Need to know where the template lives
TEMPLATE_DIR = '/opt/clovr_pipelines/workflow/project_saved_templates/megablast_tmpl'


OPTIONS = [
    ('INPUT_FILE_LIST', '', '--INPUT_FILE_LIST', 'The input file list of sequences', compose(lambda x : '${dirs.upload_dir}/tags/' + x, notNone)),
    ('REF_DB_PATH', '', '--REF_DB_PATH', 'The reference db for the blast run', compose(lambda x : '${dirs.upload_dir}/' + x, notNone)),
    ##
    # For SEQS_PER_FILE the function at the end may seem odd, but really this is just validating that they give us an int
    # we actually want it as a string in order to do the replacement in the config file, which is why we do
    # str . int
    ('SEQS_PER_FILE', '', '--SEQS_PER_FILE', 'Number of sequences per file, defaults to 1000', compose(str, int, defaultIfNone('1000'))),
    ('EXPECT', '', '--EXPECT', 'e-value cutoff, default is 1e-5', defaultIfNone('1e-5')),
    ('OTHER_OPTS', '', '--OTHER_OPTS', 'Other options to pass to blast', defaultIfNone('')),
    ('FILTER', '', '--FILTER', 'Filter query, default is T', compose(restrictValues(['T', 'F']), defaultIfNone('T')))
    ]


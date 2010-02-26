##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath

##
# Need to know where the template lives
TEMPLATE_NAME = 'total_metagenomics'


OPTIONS = [
    ('INPUT_FILE_LIST', '', '--INPUT_FILE_LIST', 'The input file list of SFF files', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('BLASTN_DB_PATH', '', '--BLASTN_DB_PATH', 'The reference db for the blastn step', compose(tagToRefDBPath, lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('BLASTP_DB_PATH', '', '--BLASTP_DB_PATH', 'The reference db for the blastp step', compose(tagToRefDBPath, lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('BLASTX_DB_PATH', '', '--BLASTX_DB_PATH', 'The reference db for the blastp step', compose(tagToRefDBPath, lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('HMMER_DB_PATH', '', '--HMMER_DB_PATH', 'The HMM db used for the hmmpfam step', compose(tagToRefDBPath, lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('HMM_INFO_FILE', '', '--HMM_INFO_FILE', 'A MLDBM file containing parsed information for the HMMer database', defaultIfNone(""))
    ]

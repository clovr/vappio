TEMPLATE_NAME = 'clovr_resistome'
##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath
TEMPLATE_NAME = 'clovr_resistome'

OPTIONS = [('input.DATASET_FILE_LIST', '', '--DATASET_FILE_LIST', 'The dataset file list of sequences to construct database', compose(lambda x : '${dirs.tag_dir}/' + x, defaultIfNone('${input.DATASET_TAG}'))), ('input.FASTA_FILE_LIST', '', '--FASTA_FILE_LIST', 'The fasta file list of sequences to query against the database', compose(lambda x : '${dirs.tag_dir}/' + x, defaultIfNone('${input.FASTA_TAG}')))]


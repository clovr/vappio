##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath

##
# Need to know where the template lives
TEMPLATE_NAME = 'clovr_metatranscriptomics'


OPTIONS = [
    ('input.FASTA_TAG', '', '--FASTA_TAG', 'The input file list of fasta files', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('input.MAPPING_TAG', '', '--MAPPING_TAG', 'The mapping file for all fastas', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)), 
    ('input.NUCLEOTIDE_DB_PATH', '', '--NUCLEOTIDE_DB_PATH', 'The root nucelotide database path', compose(lambda x : '${dirs.upload_dir}/' + x, notNone)),
    ('input.PROTEIN_DB_PATH', '', '--PROTEIN_DB_PATH', 'The root protein database path', compose(lambda x : '${dirs.upload_dir}/' + x, notNone)),
    ('input.RRNA_DB_PATH', '', '--RRNA_DB_PATH', 'The root rRNA database path', compose(lambda x : '${dirs.upload_dir}/' + x, notNone)),
    ('params.TOTAL_FILES','', '--TOTAL_FILES', 'Tell split_multifasta to produce exactly this amount of files', defaultIfNone("")),
    ('params.GROUP_COUNT', '', '--GROUP_COUNT', 'Group count to use in Ergatis', defaultIfNone("50"))
    ]

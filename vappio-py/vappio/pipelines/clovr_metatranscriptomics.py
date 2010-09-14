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
    ('INPUT_FILE_LIST', '', '--INPUT_FILE_LIST', 'The input file list of fasta files', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('MAPPING_FILE', '', '--MAPPING_FILE', 'The mapping file for all fastas', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)), 
    ('NUCLEOTIDE_DB_PATH', '', '--NUCLEOTIDE_DB_PATH', 'The root nucelotide database path', compose(lambda x : '${dirs.upload_dir}/' + x, notNone)),
    ('PROTEIN_DB_PATH', '', '--PROTEIN_DB_PATH', 'The root protein database path', compose(lambda x : '${dirs.upload_dir}/' + x, notNone)),
    ('RRNA_DB_PATH', '', '--RRNA_DB_PATH', 'The root rRNA database path', compose(lambda x : '${dirs.upload_dir}/' + x, notNone)),
    ('SEQS_PER_FILE', '', '--SEQS_PER_FILE', 'Number of sequences per file produced by split_multifasta', defaultIfNone("")),
    ('CUTOFF', '', '--CUTOFF', 'Metagene gene calls below this nucleotide length are discarded', defaultIfNone("")),
    ('TOTAL_FILES','', '--TOTAL_FILES', 'Tell split_multifasta to produce exactly this amount of files', defaultIfNone("")),
    ('NUM_SEQS', '', '--NUM_SEQS', 'Number of sequences per bsml file produced by metagene', defaultIfNone("150")),
    ('GROUP_COUNT', '', '--GROUP_COUNT', 'Group count to use in Ergatis', defaultIfNone("50"))
    ]
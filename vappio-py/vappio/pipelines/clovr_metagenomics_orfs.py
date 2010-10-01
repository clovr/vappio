##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath

##
# Need to know where the template lives
TEMPLATE_NAME = 'clovr_metagenomics_orfs'


OPTIONS = [
    ('input.FASTA_FILE_LIST', '', '--FASTA_TAG', 'The input file list of FASTA files', compose(lambda x : '${dirs.tag_dir}/' + x, defaultIfNone('${input.FASTA_TAG}'))),
    ('input.MAPPING_FILE_LIST', '', '--MAPPING_TAG', 'Mapping data file', compose(lambda x : '${dirs.tag_dir}/' + x, defaultIfNone('${input.MAPPING_TAG}'))), 
    ('input.NUCLEOTIDE_DB_FILE_LIST', '', '--NUCLEOTIDE_DB_TAG', 'The root nucelotide database path', compose(lambda x : '${dirs.upload_dir}/' + x, defaultIfNone('${input.NUCLEOTIDE_DB_TAG}'))),
    ('input.PROTEIN_DB_FILE_LIST', '', '--PROTEIN_DB_TAG', 'The root protein database path', compose(lambda x : '${dirs.upload_dir}/' + x, defaultIfNone('${input.PROTEIN_DB_TAG}'))),
    ('params.TOTAL_FILES','', '--TOTAL_FILES', 'Tell split_multifasta to produce exactly this amount of files', defaultIfNone("")),
    ('params.NUM_SEQS', '', '--NUM_SEQS', 'Number of sequences per bsml file produced by metagene', defaultIfNone("150")),
    ('params.GROUP_COUNT', '', '--GROUP_COUNT', 'Group count to use in Ergatis', defaultIfNone("50"))
    ]

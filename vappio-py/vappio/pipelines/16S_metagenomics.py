##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues

from vappio.pipeline_tools.blast import tagToRefDBPath

##
# Need to know where the template lives
TEMPLATE_NAME = '16S_metagenomics'


OPTIONS = [
    ('INPUT_FILE_LIST', '', '--INPUT_FILE_LIST', 'The input file list of FASTA files', compose(lambda x : '${dirs.tag_dir}/' + x, notNone)),
    ('OLIGOS_FILE', '', '--OLIGOS_FILE', 'Oligo\'s file containing barcodes, forward and reverse primers', notNone),
    ('ALIGN_DB', '', '--ALIGN_DB', 'Database used by mothur\'s align.seqs', compose(lambda x : '${dirs.upload_dir}/' + x, notNone)),
    ('CLASSIFY_DB', '', '--CLASSIFY_DB', 'Database used by mothur\'s classify.seqs', compose(lambda x : '${dirs.upload_dir}/' + x, notNone)),
    ('TAXONOMY_DB', '', '--TAXONOMY_DB', 'Taxonomy database used by mothur\'s classify.seqs', compose(lambda x : '${dirs.upload_dir}/' + x, notNone))
    ]

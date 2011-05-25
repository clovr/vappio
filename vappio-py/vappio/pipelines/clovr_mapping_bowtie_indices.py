##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os
import re

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues, composeCLI, notBlank

from vappio.pipeline_tools.blast import tagToRefDBPath

TEMPLATE_NAME = 'clovr_mapping_bowtie_indices'

OPTIONS = [
    ('input.PAIRED_READS_LIST', '', '--PAIRED_READS_LIST', 'A comma separated list of input tags referencing paired-end data. Each tag should contain two files.', composeCLI( lambda x : ','.join(['${dirs.tag_dir}/' + y for y in x and re.split('[\s,]+', x) or []]), defaultIfNone('${input.INPUT_PAIRED_TAG}'))),
    ('input.READS_LIST', '', '--READS_LIST', 'A comma separated list of input tags referencing non-paired data.', composeCLI( lambda x : ','.join(['${dirs.tag_dir}/' + y for y in x and re.split('[\s,]+', x) or []]), defaultIfNone('${input.INPUT_READS_TAG}') ) ),
    ('input.REFERENCE_DB_PATH', '', '--REFERENCE_DB_PATH', 'The input reference bowtie-build generated indices', composeCLI(tagToRefDBPath, lambda x : os.path.join('${dirs.tag_dir}/', x), notBlank, defaultIfNone('${input.REFERENCE_TAG}'))),
    ('params.MAX_INSERT_SIZE', '', '--MAX_INSERT_SIZE', 'Bowtie maximum insert size', defaultIfNone("300")),
    ('params.MAX_MISMATCHES', '', '--MAX_MISMATCHES', 'Bowtie maximum number of mismatches', defaultIfNone("2")),
    ('params.MAX_ALIGNS_PER_READ', '', '--MAX_ALIGNS_PER_READ', 'Bowtie maximum number of alignments per read.', defaultIfNone("1")),
    ('params.BOWTIE_OPTS', '', '--BOWTIE_OPTS', 'Any other bowtie command-line arguments', defaultIfNone(""))
    ]

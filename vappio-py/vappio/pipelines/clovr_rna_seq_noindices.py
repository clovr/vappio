##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os
import re

from igs.utils.functional import identity, compose
from igs.utils.cli import notNone, defaultIfNone, restrictValues, composeCLI, notBlank
from vappio.pipeline_tools.blast import tagToRefDBPath

##
# Need to know where the template lives
TEMPLATE_NAME = 'clovr_rna_seq_noindices'

OPTIONS = [
        ('input.PAIRED_READS_LIST', '', '--PAIRED_READS_LIST', 'A comma separated list of input tags referencing paired-end data. Each tag should contain two files.', composeCLI( lambda x : ','.join(['${dirs.tag_dir}/' + y for y in x and re.split('[\s,]+', x) or []]), defaultIfNone('${input.INPUT_PAIRED_TAG}'))),
        ('input.READS_LIST', '', '--READS_LIST', 'A comma separated list of input tags referencing non-paired data.', composeCLI( lambda x : ','.join(['${dirs.tag_dir}/' + y for y in x and re.split('[\s,]+', x) or []]), defaultIfNone('${input.INPUT_READS_TAG}') ) ),
        ('input.REFERENCE_FILE_LIST', '', '--REFERENCE_FILE_LIST', 'The input reference bowtie-build generated indices', compose(lambda x : os.path.join('${dirs.tag_dir}/', x), notBlank, defaultIfNone('${input.REFERENCE_TAG}'))),
        ('input.GFF3_FILE_LIST', '', '--GFF3_FILE_LIST', 'GFF3 file containing reference sequence and annotations', compose(lambda x : '${dirs.tag_dir}/' + x, defaultIfNone('${input.INPUT_GFF3_TAG}'))),
        ('input.INPUT_SAMPLE_MAP_FILE_LIST', '', '--INPUT_SAMPLE_MAP_FILE_LIST', 'Tab-delimeted file usedd to map the read count files to the appropriate phenotype and replicate.', compose(lambda x : '${dirs.tag_dir}/' + x, defaultIfNone('${input.INPUT_SAMPLE_MAP_TAG}'))),
        ('params.MAX_INSERT_SIZE', '', '--MAX_INSERT_SIZE', 'Bowtie maximum insert size', defaultIfNone("300")),
        ('params.MAX_MISMATCHES', '', '--MAX_MISMATCHES', 'Bowtie maximum number of mismatches', defaultIfNone("2")),
        ('params.MAX_ALIGNS_PER_READ', '', '--MAX_ALIGNS_PER_READ', 'Bowtie maximum number of alignments per read.', defaultIfNone("1")),
        ('params.BOWTIE_OPTS', '', '--BOWTIE_OPTS', 'Any other bowtie command-line arguments', defaultIfNone("")),
        ('params.COUNT_MODE', '', '--COUNT_MODE', 'Scheme to decipher overlapping features and reads', compose(restrictValues(['union', 'intersection-strict', 'intersection-nonempty']), defaultIfNone("union"))),
        ('params.COUNTING_FEATURE', '', '--COUNTING_FEATURE', 'Feature type to extract from gtf file and count over', notNone),
        ('params.MIN_ALIGN_QUAL', '', '--MIN_ALIGN_QUAL', 'Minimum quality of alignment required to count a read', defaultIfNone(0)),
        ('params.IS_STRANDED', '', '--IS_STRANDED', 'Minimum quality of alignment required to count a read', compose(restrictValues(['yes', 'no']), defaultIfNone('no'))),
        ('params.ID_ATTRIBUTE', '', '--ID_ATTRIBUTE', 'Attribute upon which to group features on when counting reads', notNone)
    ]

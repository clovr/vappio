from vappio.webservice import tag

from igs.utils import seq_file_format

FILE_TYPES = {'fasta': seq_file_format.isFasta,
              'sff': seq_file_format.isSFF,
              'fastq': seq_file_format.isFastq,
              'genbank': seq_file_format.isGenbank
              }

def tags_is_filetype(tags, filetype):
    if filetype not in FILE_TYPES:
        raise Exception('Unknown file type')

    tagInfo = tag.listTags('localhost',
                           'local',
                           {'$or': [{'tag_name': t} for t in tags]},
                           True)

    for t in tagInfo:
        if t['files']:
            for f in t['files']:
                if not FILE_TYPES[filetype](f):
                    raise Exception('File %s did not pass' % f)
        elif not t['phantom'] and ('urls' not in t['metadata'] or 'urls' in t['metadata'] and t['metadata'].get('urls_realized', False)):
            raise Exception('A none-phantom-none-urls tag with no files is of no type')

    

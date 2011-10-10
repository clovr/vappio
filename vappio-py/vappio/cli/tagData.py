#!/usr/bin/env python
import sys
import os

from igs.utils import cli
from igs.utils import functional as func

from vappio.webservice.tag import tagData

from vappio.tasks.utils import runTaskStatus

OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', cli.defaultIfNone('localhost')),
    ('cluster', '', '--cluster', 'Name of cluster, defaults to local', cli.defaultIfNone('local')),
    ('tag_name', '', '--tag-name', 'Name of tag', cli.notNone),
    ('urls', '', '--url', 'URLs to download, multiple --url flags can be specified', cli.defaultIfNone([]), cli.LIST),
    ('stdin', '', '--stdin', 'Take list of files from stdin rather than arguments on command line', cli.defaultIfNone(False), cli.BINARY),
    ('tag_base_dir', '', '--tag-base-dir', 'Base directory of the tag', func.identity),
    ('recursive', '-r', '--recursive', 'Recursively include directories', cli.defaultIfNone(False), cli.BINARY),
    ('expand', '-e', '--expand', 'Expand archives', cli.defaultIfNone(False), cli.BINARY),
    ('compress', '-c', '--compress',
     'Make a tarball of the tagged results.  This should be the directory to put the tarball. This is not mutually exclusive with --expand',
     func.identity),
    ('append', '-a', '--append', 'Append listed files to tag name, ignoring duplicate files', cli.defaultIfNone(False), cli.BINARY),
    ('overwrite', '-o', '--overwrite', 'Overwrite file list if it exists', cli.defaultIfNone(False), cli.BINARY),
    ('block', '-b', '--block', 'Block on the tagging', cli.defaultIfNone(False), cli.BINARY),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end', cli.defaultIfNone(False), cli.BINARY),
    ('metadata', '-m', '',
     'Add metadata in a key=value notation.  Multiple options are valid.  Ex: -m filetype=fasta -m usage=referencedb',
     cli.defaultIfNone([]),
     cli.LIST)
    ]


def _makeAbsolute(fname):
    """
    Makes a file name absolute by prepending the current working directory to it
    if it does not start with '/'
    """
    if fname[0] != '/':
        return os.path.join(os.getcwd(), fname)
    else:
        return fname

def main(options, files):
    metadata = dict([s.split('=', 1) for s in options('general.metadata')])
    if options('general.tag_base_dir'):
        metadata['tag_base_dir'] = options('general.tag_base_dir')

    if options('general.append') and not options('general.overwrite'):
        action = 'append'
    elif not options('general.append') and options('general.overwrite'):
        action = 'overwrite'
    elif not options('general.append') and not options('general.overwrite'):
        action = 'create'
    else:
        raise Exception('--append and --overwrite are mutually exclusive')

    if options('general.stdin'):
        files = [f.strip() for f in sys.stdin.readlines()]
    
    tag = tagData(options('general.host'),
                  options('general.cluster'),
                  action,
                  options('general.tag_name'),
                  [_makeAbsolute(f) for f in files],
                  options('general.urls'),
                  metadata,
                  options('general.recursive'),
                  options('general.expand'),
                  options('general.compress') and _makeAbsolute(options('general.compress')) or None)


    if options('general.print_task_name'):
        print tag['task_name']
    else:
        runTaskStatus(tag['task_name'], options('general.cluster'))
    

if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS, usage='--name=cluster --tag-name=name [options] file_1 .. file_n'))
    


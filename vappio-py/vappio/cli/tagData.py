#!/usr/bin/env python
import os

from igs.utils import cli
from igs.utils import functional as func

from vappio.webservice.tag import tagData

from vappio.tasks.task import TASK_FAILED
from vappio.tasks.utils import blockOnTask

OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', cli.defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster, defaults to local', cli.defaultIfNone('local')),
    ('tag_name', '', '--tag-name', 'Name of tag', cli.notNone),
    ('tag_base_dir', '', '--tag-base-dir', 'Base directory of the tag', func.identity),
    ('recursive', '-r', '--recursive', 'Recursively include directories', cli.defaultIfNone(False), cli.BINARY),
    ('expand', '-e', '--expand', 'Expand archives', cli.defaultIfNone(False), cli.BINARY),
    ('append', '-a', '--append', 'Append listed files to tag name, ignoring duplicate files', cli.defaultIfNone(False), cli.BINARY),
    ('overwrite', '-o', '--overwrite', 'Overwrite file list if it exists', cli.defaultIfNone(False), cli.BINARY),
    ('block', '-b', '--block', 'Block on the tagging', cli.defaultIfNone(False), cli.BINARY),
    ('print_task_name', '-t', '--print-task-name', 'Print the name of the task at the end', cli.defaultIfNone(False), cli.BINARY),
    ('metadata', '-m', '',
     'Add metadata in a key=value notation.  Multiple options are valid.  Ex: -m filetype=fasta -m usage=referencedb',
     cli.defaultIfNone([]),
     cli.LIST)
    ]


def makeAbsolute(fname):
    """
    Makes a file name absolute by prepending the current working directory to it
    if it does not start with '/'
    """
    if fname[0] != '/':
        return os.path.join(os.getcwd(), fname)
    else:
        return fname

def main(options, files):
    taskName = tagData(options('general.host'),
                       options('general.name'),
                       options('general.tag_name'),
                       options('general.tag_base_dir'),
                       [makeAbsolute(f) for f in files],
                       options('general.recursive'),
                       options('general.expand'),
                       options('general.append'),
                       options('general.overwrite'),
                       dict([s.split('=', 1) for s in options('general.metadata')]))

    if options('general.block'):
        state = blockOnTask(options('general.host'), options('general.name'), taskName)
        if state == TASK_FAILED:
            raise Exception('Tagging data failed')

    if options('general.print_task_name'):
        print taskName
    
    

if __name__ == '__main__':
    main(*cli.buildConfigN(OPTIONS, usage='--name=cluster --tag-name=name [options] file_1 .. file_n'))
    


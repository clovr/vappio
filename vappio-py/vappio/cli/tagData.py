#!/usr/bin/env python
import os

from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.functional import identity

from vappio.webservice.tag import tagData

from vappio.tasks.task import TASK_FAILED
from vappio.tasks.utils import blockOnTask

OPTIONS = [
    ('host', '', '--host', 'Host of web services to connect to, defaults to local host', defaultIfNone('localhost')),
    ('name', '', '--name', 'Name of cluster, defaults to local', defaultIfNone('local')),
    ('tag_name', '', '--tag-name', 'Name of tag', notNone),
    ('tag_base_dir', '', '--tag-base-dir', 'Base directory of the tag', identity),
    ('recursive', '-r', '--recursive', 'Recursively include directories', defaultIfNone(False), True),
    ('expand', '-e', '--expand', 'Expand archives', defaultIfNone(False), True),
    ('append', '-a', '--append', 'Append listed files to tag name, ignoring duplicate files', defaultIfNone(False), True),
    ('overwrite', '-o', '--overwrite', 'Overwrite file list if it exists', defaultIfNone(False), True),
    ('block', '-b', '--block', 'Block on the tagging', defaultIfNone(False), True),
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
                       options('general.overwrite'))

    if options('general.block'):
        state = blockOnTask(options('general.host'), options('general.name'), taskName)
        if state == TASK_FAILED:
            raise Exception('Tagging data filed')
    
    

if __name__ == '__main__':
    main(*buildConfigN(OPTIONS, usage='--name=cluster --tag-name=name [options] file_1 .. file_n'))
    


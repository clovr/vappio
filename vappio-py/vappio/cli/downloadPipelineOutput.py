#!/usr/bin/env python
from igs.utils.cli import buildConfigN, notNone, defaultIfNone
from igs.utils.functional import identity

from vappio.webservice.pipeline import downloadPipelineOutput

from vappio.tasks.task import TASK_FAILED
from vappio.tasks.utils import blockOnTask

OPTIONS = [
    ('host', '', '--host', 'Host of webservice to contact', defaultIfNone('localhost')),    
    ('name', '', '--name', 'Name of cluster', notNone),
    ##
    # Want to make sure this is an int but we want it as a string later in the program
    ('pipeline', '-p', '--pipeline-name', 'Name of pipeline', notNone),
    ('output_dir', '-o', '--output-dir', 'Directory the output file should go to', notNone),
    ('overwrite', '', '--overwrite', 'Do you want to overwrite a local file if it already exists?', defaultIfNone(False), True),
    ('block', '-b', '--block', 'Block until download is complete', identity, True),
    ]



def main(options, _args):
    taskName = downloadPipelineOutput(options('general.host'),
                                      options('general.name'),
                                      options('general.pipeline'),
                                      options('general.output_dir'),
                                      options('general.overwrite'))

    if options('general.block'):
        state = blockOnTask('localhost', 'local', taskName)
        if state == TASK_FAILED:
            raise Exception('Starting cluster failed')
    
    
if __name__ == '__main__':
    main(*buildConfigN(OPTIONS))

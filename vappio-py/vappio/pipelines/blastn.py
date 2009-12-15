##
# This handles running a blastn pipeline
# THIS SHOULD BE RUN ON THE REMOTE SIDE
import os
import time
import optparse

from igs.utils.cli import buildConfig, MissingOptionError
from igs.utils.config import configFromMap, replaceStr
from igs.utils.commands import runSystemEx


TEMPLATE_DIR = '/opt/clovr_pipelines/workflow/project_saved_templates/blastn_tmpl'
TEMPLATE_CONFIG = os.path.join(TEMPLATE_DIR, 'blastn.config')
TEMPLATE_LAYOUT = os.path.join(TEMPLATE_DIR, 'pipeline.layout')

def cliParser():
    parser = optparse.OptionParser()

    parser.add_option('', '--input_flist', dest='input_flist', help='File list for input')
    parser.add_option('', '--refdb', dest='refdb', help='Reference DB')

    return parser


def cliMerger(cliOptions, _args):
    return configFromMap({
        'input_flist': cliOptions.input_flist,
        'refdb': cliOptions.refdb,
        })



def _runPipeline(options):
    conf = configFromMap({
        'INPUT_FILE_LIST': options('input_flist'),
        'REF_DB_PATH': options('refdb')
        })

    foutName = os.path.join('/tmp', str(time.time()))
    fout = open(foutName, 'w')
    for line in open(TEMPLATE_CONFIG):
        fout.write(replaceStr(line, conf))

    fout.close()

    runSystemEx('run_pipeline.pl --config=%(config)s --templatelayout=%(templatelayout)s' % dict(
        config=foutName,
        templatelayout=TEMPLATE_LAYOUT))
    

def runPipeline():
    _runPipeline(buildConfig(cliParser(), cliMerger))

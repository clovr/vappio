##
# Functions to control creating and running a pipeline through ergatis
import optparse
import os
import time


from igs.utils.config import configFromMap, replaceStr

from igs.utils.commands import runSystemEx


def buildCliParser(options):
    parser = optparse.OptionParser()

    for n, _, desc in options:
        parser.add_option('', '--' + n, dest=n, help=desc)

    return parser

def runPipeline(pipeline):
    """
    Takes a pipeline which is some sort of object
    which has:

    TEMPLATE_DIR - where the template lives
    OPTIONS - list of options needed for config file

    OPTIONS looks like (name, func, description):
    name - the name they will pass on the command line, this also matches the name of the variable in
           the config file
    func - A functiont hat is applied to the option from the command line, if nothing needs to be
           done simply use igs.utils.functional.id
    description - Just a brief description of the variable, this will be in the --help for the pipeline
    """
    
    parser = buildCliParser(pipeline.OPTIONS)

    options, _args = parser.parse_args()

    conf = configFromMap(dict([(n, f(getattr(options, n))) for n, f, _d in pipeline.OPTIONS]))

    templateConfig = os.path.join(pipeline.TEMPLATE_DIR, 'pipeline_tmpl.config')
    templateLayout = os.path.join(pipeline.TEMPLATE_DIR, 'pipeline.layout')

    foutName = os.path.join('/tmp', str(time.time()))
    fout = open(foutName, 'w')
    for line in open(templateConfig):
        fout.write(replaceStr(line, conf))
        
    fout.close()
        
    runSystemEx('run_pipeline.pl --config=%(config)s --templatelayout=%(templatelayout)s' % dict(
        config=foutName,
        templatelayout=templateLayout))

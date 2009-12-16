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

    TEMPLATE_CONFIG
    TEMPLATE_LAYOUT
    OPTIONS
    """
    
    parser = buildCliParser(pipeline.OPTIONS)

    options, _args = parser.parse_args()

    conf = configFromMap(dict([(n, f(getattr(options, n))) for n, f, _d in pipeline.OPTIONS]))


    foutName = os.path.join('/tmp', str(time.time()))
    fout = open(foutName, 'w')
    for line in open(pipeline.TEMPLATE_CONFIG):
        fout.write(replaceStr(line, conf))
        
    fout.close()
        
    runSystemEx('run_pipeline.pl --config=%(config)s --templatelayout=%(templatelayout)s' % dict(
        config=foutName,
        templatelayout=pipeline.TEMPLATE_LAYOUT))

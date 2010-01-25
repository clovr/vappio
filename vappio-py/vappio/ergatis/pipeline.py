##
# Functions to control creating and running a pipeline through ergatis
import optparse
import os
import time


from igs.utils.cli import buildConfigN
from igs.utils.config import replaceStr
from igs.utils.commands import runSingleProgram, ProgramRunError


def runPipeline(pipeline, args=None):
    """
    args are any CLI arguments you want to use instead of
    whatever is in sys.argv

    This should be refactored to not rely on args in this way
    
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

    ##
    # Mocheezmo way to have it load a conf file.  This will be removed in the future
    options = pipeline.OPTIONS
    options.append(('conf', '', '--conf', 'Conf file', lambda _ : '/tmp/machine.conf'))
    
    conf, _args = buildConfigN(options, args, putInGeneral=False)

    templateDir = os.path.join(conf('dirs.clovr_pipelines_template_dir'), pipeline.TEMPLATE_NAME)
    templateConfig = os.path.join(templateDir, 'pipeline_tmpl.config')
    templateLayout = os.path.join(templateDir, 'pipeline.layout')

    foutName = os.path.join('/tmp', str(time.time()))
    fout = open(foutName, 'w')
    for line in open(templateConfig):
        fout.write(replaceStr(line, conf))
        
    fout.close()

    cmd = 'run_pipeline.pl --config=%(config)s --templatelayout=%(templatelayout)s' % dict(
        config=foutName,
        templatelayout=templateLayout)

    res = []
    exitCode = runSingleProgram(cmd, res.append)

    ##
    # If we got a weird exit code or more than one line was print or nothing was printed
    # then something bad happened
    if exitCode != 0 or len(res) > 1 or not res:
        raise ProgramRunError(cmd, exitCode)

    ##
    # This should be the pipeline ID
    return res[0].strip()
        

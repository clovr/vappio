import os
import StringIO

from twisted.python import log

from twisted.internet import defer

from igs_tx.utils import global_state
from igs_tx.utils import commands

def _addPipelineConfigToComponent(componentConfig, pipelineConfig, newComponentConfig):
    fout = open(newComponentConfig, 'w')
    fin = open(componentConfig)
    for line in fin:
        fout.write(line)
        if line.strip() == '[include]':
            fout.write('$;USER_CONFIG$;=' + pipelineConfig + '\n')

    fout.close()
    fin.close()


def _replaceComponentConfigKeys(componentConfig, outComponentConfig):
    return commands.runProcess(['replace_config_keys',
                                '--template_conf', componentConfig,
                                '--output_conf', outComponentConfig],
                               log=True)

def _replaceTemplateKeys(templateXml, componentConfig, instanceXml):
    return commands.runProcess(['replace_template_keys',
                                '--template_xml', templateXml,
                                '--component_conf', componentConfig,
                                '--output_xml', instanceXml],
                               log=True)

def _runWorkflow(instanceXml):
    stderr = StringIO.StringIO()

    cmd = ['RunWorkflow',
           '-i', instanceXml,
           '-m', '1',
           '--init-heap=100m',
           '--max-heap=1024m',
           '--logconf=/opt/workflow-sforge/log4j.properties',
           '--debug']
    
    def _raiseProgramError(_):
        raise commands.ProgramRunError(cmd, stderr.getvalue())
    
    return commands.runProcess(cmd,
                               stderrf=stderr.write,
                               log=True).addErrback(_raiseProgramError)
    
@defer.inlineCallbacks
def run(componentConfig, templateXml, pipelineConfig, tmpDir):
    # First, add pipelineConfig to the componentConfig in the corrrect place
    newComponentConfig = os.path.join(tmpDir, 'component-' + global_state.make_ref() + '.conf')
    replacedComponentConfig = os.path.join(tmpDir, 'replacedcomponent-' + global_state.make_ref() + '.conf')
    instanceXml = os.path.join(tmpDir, global_state.make_ref() + '.xml')

    _addPipelineConfigToComponent(componentConfig, pipelineConfig, newComponentConfig)
    yield _replaceComponentConfigKeys(newComponentConfig, replacedComponentConfig)
    yield _replaceTemplateKeys(templateXml, replacedComponentConfig, instanceXml)
    yield _runWorkflow(instanceXml)

    os.unlink(newComponentConfig)
    os.unlink(replacedComponentConfig)
    os.unlink(instanceXml)

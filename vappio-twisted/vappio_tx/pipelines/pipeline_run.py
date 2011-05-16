import os
import time
import StringIO

from twisted.internet import defer

from igs.utils import config

from igs_tx.utils import commands

def handleIncludes(sin):
    lines = [l.strip() for l in sin]
    sections = set([s[1:-1] for s in lines if s and s[0] == '[' and s[-1] == ']'])
 
    for line in lines:
        if line.startswith('-include'):
            includeLines = list(handleIncludes(open(line.split('=')[1])))
            includeSections = set([s[1:-1] for s in includeLines if s and s[0] == '[' and s[-1] == ']'])
            overlappingSections = sections.intersection(includeSections)
            ignoreSection = False
    
            for l in includeLines:
                if l and l[0] == '[' and l[-1] == ']' and l[1:-1] in overlappingSections:
                    ignoreSection = True
                elif l and l[0] == '[' and l[-1] == ']':
                    ignoreSection = False
 
                if not ignoreSection:
                    yield l
 
            # Once we have looped through all our lines we want to regenerate our sections 
            # list containing all unique sections
            sections.update(includeSections)
    
        else:
            yield line


@defer.inlineCallbacks
def run(state, pipeline):
    tmpConfigName = os.path.join('/tmp', str(time.time()) + '.config')

    pipeline.config = config.configFromMap({'CONFIG_FILE': tmpConfigName},
                                           base=pipeline.config)
    
    fout = open(tmpConfigName, 'w')
    
    # We want to produce an ini like file with [section]'s
    sections = {}
    for k in pipeline.config.keys():
        sections.setdefault('.'.join(k.split('.')[:-1]), []).append(k)

    for s, ks in sections.iteritems():
        if s not in ['', 'env']:        
            fout.write('[' + s + ']\n')
            for k in ks:
                shortK = k.split('.')[-1]
                fout.write('%s=%s\n' % (shortK, str(pipeline.config(k))))

    fout.close()

    templateDir = os.path.join(state.machineconf('dirs.clovr_pipelines_template_dir'),
                               pipeline.protocol)
    templateConfig = os.path.join(templateDir, 'pipeline_tmpl.config')
    templateLayout = os.path.join(templateDir, 'pipeline.layout')

    tmpPipelineConfig = os.path.join('/tmp', str(time.time()) + '.pipeline.config')
    fout = open(tmpPipelineConfig, 'w')
    for line in handleIncludes(open(templateConfig)):
        fout.write(config.replaceStr(line, pipeline.config) + '\n')

    fout.close()

    cmd = ['run_pipeline.pl',
           '--config=' + tmpPipelineConfig,
           '--templatelayout=' + templateLayout,
           '--taskname=' + pipeline.taskName]

    if pipeline.queue:
        cmd.append('--queue=' + pipeline.queue)

    
    stdout = StringIO.StringIO()
    stderr = StringIO.StringIO()
    
    yield commands.runProcess(cmd,
                              stdoutf=stdout.write,
                              stderrf=stderr.write)

    pipelineId = stdout.getvalue()
    if not pipelineId:
        raise commands.ProgramRunError(cmd, stderr.getvalue())

    defer.returnValue(pipeline.update(pipelineId=pipelineId))
    
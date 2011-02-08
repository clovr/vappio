##
# Functions to control creating and running a pipeline through ergatis
import os
import time
from xml.dom import minidom

from twisted.python import reflect

from igs.utils.core import getStrBetween
from igs.utils import cli
from igs.utils.functional import identity, const, applyIfCallable, Record
from igs.utils import config #import replaceStr, configFromStream, configFromMap, configToDict
from igs.utils.commands import runSingleProgram, ProgramRunError

from igs.xml.xmlquery import execQuery, name

from vappio.pipeline_tools import persist


class PipelineError(Exception):
    pass


class Pipeline(Record):
    """
    Represents a pipeline
    """

    def state(self):
        """
        Returns the state of the pipeline
        """
        path = os.path.join(self.config('dirs.pipeline_runtime'), str(self.pid), 'pipeline.xml')
        for line in open(path):
            if '<state>' in line:
                return getStrBetween(line, '<state>', '</state>')

        raise PipelineError('Could not find <state> in the pipeline.xml')

    def progress(self):
        """
        Returns a tuple of (number of completed tasks, total tasks)
        """
        doc = minidom.parse(os.path.join(self.config('dirs.pipeline_runtime'), str(self.pid), 'pipeline.xml'))
        query = [name('commandSetRoot'),
                 [name('commandSet'),
                  [name('status')]]]

        res = execQuery(query, doc)
        total = sum([int(r.childNodes[0].data) for r in res if r.localName == 'total'])
        complete = sum([int(r.childNodes[0].data) for r in res if r.localName == 'complete'])

        return (complete, total)

    def ptypeStr(self):
        """
        A string representing the ptype
        """
        return reflect.fullyQualifiedName(self.ptype).split('.')[-1]



class PipelineSnapshot(Record):
    """
    Represents a pipeline at a particular point in time so it can be transfered around
    """


    def ptypeStr(self):
        """
        A string representing the ptype
        """
        return reflect.fullyQualifiedName(self.ptype).split('.')[-1]
    
    
def createPipeline(taskName, name, pid, ptype, config):
    return Pipeline(name=name,
                    taskName=taskName,
                    pid=pid,
                    ptype=ptype,
                    config=config)


def createPipelineSS(pipeline):
    complete, total = pipeline.progress()
    state = pipeline.state()
    return PipelineSnapshot(name=pipeline.name,
                            taskName=pipeline.taskName,
                            pid=pipeline.pid,
                            ptype=pipeline.ptype,
                            config=pipeline.config,
                            complete=complete,
                            total=total,
                            state=state)

def pipelineToDict(p):
    return dict(name=p.name,
                taskName=p.taskName,
                pid=p.pid,
                ptype=p.ptypeStr(),
                config=[kv for kv in config.configToDict(p.config).iteritems()])

def pipelineFromDict(d):
    return createPipeline(taskName=d['taskName'],
                          name=d['name'],
                          pid=d['pid'],
                          ptype=reflect.namedAny('vappio.pipelines.' + d['ptype']),
                          config=config.configFromMap(dict(d['config'])))


def loadAllPipelines():
    return [pipelineFromDict(p) for p in persist.loadAll()]

def loadPipeline(name):
    return pipelineFromDict(persist.load(name))

def savePipeline(p):
    return persist.dump(pipelineToDict(p))

def pipelineSSToDict(pss):
    return dict(name=pss.name,
                taskName=pss.taskName,
                pid=pss.pid,
                ptype=pss.ptypeStr(),
                config=config.configToDict(pss.config),
                complete=pss.complete,
                total=pss.total,
                state=pss.state)

def pipelineSSFromDict(d):
    return PipelineSnapshot(name=d['name'],
                            taskName=d['taskName'],
                            pid=d['pid'],
                            ptype=reflect.namedAny('vappio.pipelines.' + d['ptype']),
                            config=config.configFromMap(d['config']),
                            complete=d['complete'],
                            total=d['total'],
                            state=d['state'])

def confIfPipelineConfigSet(conf, options):
    """
    Takes a conf, checks to see if a pipeline conf file is specified,
    if so it loads it up and applies it OVER any options specified on
    the command line.  This may seem counter intuitive but it makes
    other things easier, for example a pipeline redefining anything
    in the machines.conf since that is also in this conf.  It then
    applies the functions in the OPTIONS variable in the values in
    the config file
    """
    if conf('CONFIG_FILE', default=None) is not None:
        fconf = config.configFromStream(open(conf('CONFIG_FILE')))
        keys = fconf.keys()
        m = {}
        for o in options:
            ##
            # Get the name of the option, it's the first element of the tuple
            name = o[0]
            f = o[4]
            if name in keys:
                m[name] = applyIfCallable(f(fconf(name)), conf)

        ##
        # lazy=True is for saftey incase there is a value in the CONFIG_FILE that we use that
        # really depends on a value in the map we just created
        return config.configFromMap(m, config.configFromStream(open(conf('CONFIG_FILE')), conf, lazy=False))
    else:
        return conf

def runPipeline(taskName, name, pipeline, args=None, queue=None):
    """
    Runes a pipeline with command line arguments in args
    
    taskName - the name of the task to update as the pipeline runs
    
    name is the name of this pipeline
    
    args are any CLI arguments you want to use instead of
    whatever is in sys.argv

    This should be refactored to not rely on args in this way
    
    Takes a pipeline which is some sort of object
    which has:

    TEMPLATE_DIR - where the template lives
    OPTIONS - list of options needed for config file

    """

    ##
    # Mocheezmo way to have it load a conf file.  This will be removed in the future
    options = list(pipeline.OPTIONS)
    options.append(('conf', '', '--conf', 'Conf file (DO NOT SPECIFY, FOR INTERNAL USE)', const('/tmp/machine.conf')))
    options.append(('CONFIG_FILE', '-c', '--CONFIG_FILE',
                    'Config file for the pipeline.  Specify this if you do not want to specify options on the comamnd line', identity))
    
    conf, _args = cli.buildConfigN(options, args, putInGeneral=False)

    ##
    # If they specified a pipeline_conf, load that and set the values
    conf = confIfPipelineConfigSet(conf, pipeline.OPTIONS)

    return runPipelineWithConfig(taskName, name, pipeline, conf, queue)



def runPipelineConfig(taskName, name, pipeline, conf, queue=None):
    """
    Takes a config object representing a pipeline options, validates those options
    in pipeline.OPTIONS and passes the results onto runPipelineWithConfig
    """
    ##
    # Mocheezmo way to have it load a conf file.  This will be removed in the future
    tmpConfigName = os.path.join('/tmp', str(time.time()) + '.config')
    options = list(pipeline.OPTIONS)
    options.append(('conf', '', '--conf', 'Conf file (DO NOT SPECIFY, FOR INTERNAL USE)', const('/tmp/machine.conf')))
    options.append(('CONFIG_FILE', '-c', '--CONFIG_FILE',
                    'Config file for the pipeline.  Specify this if you do not want to specify options on the comamnd line', const(tmpConfigName)))

    ##
    # Load up machine.conf and apply it to our current config
    conf = config.configFromConfig(conf, config.configFromStream(open('/tmp/machine.conf'), config.configFromEnv()), lazy=True)
    vals = {}
    for o in options:
        vals[o[0]] = cli.applyOption(conf(o[0], default=None), o, conf)

    conf = config.configFromMap(vals, conf)

    ##
    # For some ergatis trickery we then need to output this config to a temp file so ergatis can pull variables from it
    confDict = config.configToDict(conf)
    confVals = {}
    cv = [('.'.join(k.split('.')[:-1]), k.split('.')[-1], v) for k, v in confDict.iteritems()]
    for s, k, v in cv:
        confVals.setdefault(s, {})[k] = v

    fout = open(tmpConfigName, 'w')
    for s, d in confVals.iteritems():
        if s not in ['', 'env']:
            fout.write('[' + s + ']\n')
            for k, v in d.iteritems():
                fout.write('%s=%s\n' % (k, str(v)))

    fout.close()

    

    return runPipelineWithConfig(taskName, name, pipeline, conf, queue)
    

def runPipelineWithConfig(taskName, name, pipeline, conf, queue):
    """
    This is for internal use only
    """
    templateDir = os.path.join(conf('dirs.clovr_pipelines_template_dir'), pipeline.TEMPLATE_NAME)
    templateConfig = os.path.join(templateDir, 'pipeline_tmpl.config')
    templateLayout = os.path.join(templateDir, 'pipeline.layout')

    foutName = os.path.join('/tmp', str(time.time()))
    fout = open(foutName, 'w')
    for line in handleIncludes(open(templateConfig)):
        fout.write(config.replaceStr(line, conf) + '\n')
        
    fout.close()

    cmd = ['run_pipeline.pl',
           '--config=' + foutName,
           '--templatelayout=' + templateLayout,
           '--taskname=' + taskName]

    if queue:
        cmd.append('--queue=' + queue)

    cmd = ' '.join(cmd)
    res = []
    exitCode = runSingleProgram(cmd, res.append, None)

    ##
    # If we got a weird exit code or more than one line was print or nothing was printed
    # then something bad happened
    if exitCode != 0 or len(res) > 1 or not res:
        raise ProgramRunError(cmd, exitCode)

    ##
    # This should be the pipeline ID
    return createPipeline(taskName, name, res[0].strip(), pipeline, conf)
    
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
    
def resumePipeline(pipeline, queue=None):
    cmd = ['resume_pipeline.pl',
           '--pipeline_id=' + pipeline.pid,
           '--taskname=' + pipeline.taskName]

    if queue:
        cmd.append('--queue=' + queue)

    cmd = ' '.join(cmd)
    res = []
    exitCode = runSingleProgram(cmd, res.append, None)

    ##
    # If we got a weird exit code or more than one line was print or nothing was printed
    # then something bad happened
    if exitCode != 0 or len(res) > 1 or not res:
        raise ProgramRunError(cmd, exitCode)
    
    return pipeline

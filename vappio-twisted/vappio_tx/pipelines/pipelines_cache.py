from twisted.internet import defer

from igs.utils import functional as func
from igs.utils import config
from igs.utils import dependency

from igs_tx.utils import defer_work_queue
from igs_tx.utils import defer_utils

from vappio_tx.tasks import tasks as tasks_tx

from vappio_tx.www_client import tags as www_tags

from vappio_tx.utils import mongo_cache

from vappio_tx.pipelines import protocol_format
from vappio_tx.pipelines import pipeline_misc

class PipelinesCache(dependency.Dependable):
    def __init__(self, machineConf, persistManager, tagNotify):
        dependency.Dependable.__init__(self)

        self.machineConf = machineConf
        self.persistManager = persistManager
        self.tagNotify = tagNotify
        self.workQueue = defer_work_queue.DeferWorkQueue(1)

    @defer.inlineCallbacks
    def initialize(self):
        cacheId = lambda d : func.updateDict(d, {'_id': d['user_name'] +
                                                 '_' +
                                                 d['pipeline_name']})
        
        self.cache = yield mongo_cache.createCache('pipelines_cache',
                                                   cacheId)

        self.persistManager.addDependent(self)
        self.tagNotify.addDependent(self)

        pipelines = yield defer_utils.tryUntil(10,
                                               lambda : self.persistManager.loadAllPipelinesByAdmin({}),
                                               onFailure=defer_utils.sleep(2))
        for pipeline in pipelines:
            self.workQueue.add(self._pipelineToDictAndCache, 'load', pipeline)

    def release(self):
        """
        Even though it doesn't do anything async, it still returns a deferred to be
        symmetrical with initialize
        """
        self.persistManager.removeDependent(self)
        self.tagNotify.removeDependent(self)
        return defer.succeed(None)


    def invalidate(self, pipelineName, userName):
        @defer.inlineCallbacks
        def _loadAndCache():
            pipeline = yield self.persistManager.loadPipelineBy({'pipeline_name': pipelineName},
                                                                userName)
            yield self._pipelineToDictAndCache('save', pipeline)

        self.workQueue.add(_loadAndCache)
            

    def update(self, who, aspect, value):
        if who == self.persistManager:
            if aspect == 'load':
                # We don't want to do anything on load
                pass
            elif aspect == 'save':
                self.workQueue.add(self._pipelineToDictAndCache, aspect, value)
            elif aspect == 'remove':
                self.workQueue.add(self.cache.remove, value)
        elif who == self.tagNotify:
            if aspect == 'load':
                # Don't really care what anyone does when they load a tag
                pass
            elif aspect == 'save':
                self.workQueue.add(self._updateIfOutputTag, value)
            elif aspect == 'remove':
                # Invalidate any pipelines associated with this tag
                pass

    @defer.inlineCallbacks
    def pipelineToDict(self, pipeline):
        protocolConf = protocol_format.load(self.machineConf, pipeline.config('pipeline.PIPELINE_TEMPLATE'))

        inputTagsList = [pipeline.config(k).split(',')
                         for k, v in protocolConf
                         if v.get('type').split()[0] in ['dataset',
                                                         'blastdb_dataset',
                                                         'paired_dataset',
                                                         'singleton_dataset'] and pipeline.config(k)]
        inputTags = []
        for i in inputTagsList:
            inputTags.extend(i)


        possibleOutputTags = set([pipeline.pipelineName + '_' + t.strip()
                                  for t in pipeline.config('output.TAGS_TO_DOWNLOAD', default='').split(',')])

        query = [{'tag_name': t} for t in possibleOutputTags]

        tags = yield www_tags.loadTagsBy('localhost', 'local', pipeline.userName, {'$or': query}, False)

        tags = set([t['tag_name'] for t in tags])

        outputTags = list(tags & possibleOutputTags)

        pipelineTask = yield tasks_tx.loadTask(pipeline.taskName)

        pipelineWrapper = pipeline_misc.determineWrapper(self.machineConf,
                                                         pipeline.config('pipeline.PIPELINE_TEMPLATE'))

        pipelineDict = {'pipeline_id': pipeline.pipelineId,
                        'pipeline_name': pipeline.pipelineName,
                        'user_name': pipeline.userName,
                        'wrapper': pipeline.protocol == pipelineWrapper,
                        'protocol': pipeline.config('pipeline.PIPELINE_TEMPLATE'),
                        'checksum': pipeline.checksum,
                        'task_name': pipeline.taskName,
                        'queue': pipeline.queue,
                        'children': pipeline.children,
                        'state': pipelineTask.state,
                        'num_steps': pipelineTask.numTasks,
                        'num_complete': pipelineTask.completedTasks,
                        'input_tags': inputTags,
                        'output_tags': outputTags,
                        'pipeline_desc': pipeline.config('pipeline.PIPELINE_DESC', default=''),
                        'config': config.configToDict(pipeline.config, lazy=True),
                        }

        defer.returnValue(pipelineDict)

    @defer.inlineCallbacks
    def _pipelineToDictAndCache(self, aspect, pipeline):
        pipelineDict = yield self.pipelineToDict(pipeline)
        yield self.cache.save(pipelineDict)
        self.changed(aspect, pipelineDict)

    @defer.inlineCallbacks
    def _updateIfOutputTag(self, tagName):
        """
        We take a tag name and determine if it matches the name of a tag
        for any of our pipelines.
        """

        # A tag name for a pipeline has the form:
        # <pipeline name>_<output base name>
        splitTagName = tagName.split('_', 1)

        if len(splitTagName) == 2:
            pipelineName = splitTagName[0]

            pipelines = yield self.cache.query({'pipeline_name': pipelineName})

            for pipeline in pipelines:
                tagBaseNames = pipeline['config'].get('output.TAGS_TO_DOWNLOAD', '').split(',')
                possibleOutputTags = set([pipeline['pipeline_name'] + '_' + t.strip() for t in tagBaseNames])
                if tagName in possibleOutputTags:
                    pipeline['output_tags'].append(tagName)
                    yield self.cache.save(pipeline)
                    

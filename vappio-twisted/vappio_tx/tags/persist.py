import os
import json

from twisted.python import log

from twisted.internet import threads
from twisted.internet import defer

from igs.utils import functional as func
from igs.utils import config as config
from igs.utils import dependency

from igs_tx.utils import commands
from igs_tx.utils import defer_utils

class Error(Exception):
    pass

class TagNotFoundError(Error):
    pass

class Tag(func.Record):
    def __init__(self,
                 tagName,
                 files,
                 metadata,
                 phantom,
                 taskName):
        metadata = func.updateDict(metadata, {'task_name': taskName})
        func.Record.__init__(self,
                             tagName=tagName,
                             files=files,
                             metadata=metadata,
                             phantom=phantom,
                             taskName=taskName)

def tagToDict(t):
    return {'tag_name': t.tagName,
            'files': t.files,
            'metadata': dict(t.metadata),
            'phantom': config.configToDict(t.phantom) if t.phantom else None,
            'task_name': t.taskName}

def tagFromDict(d):
    return Tag(tagName=d['tag_name'],
               files=d['files'],
               metadata=dict(t.metadata),
               phantom=config.configFromMap(d['phantom']) if d['phantom'] else None,
               taskName=t.metadata.get('task_name'))


def _createTagPath(conf, tagName):
    return os.path.join(conf('tags.tags_directory'), tagName)




class TagPersistManager(dependency.Dependable):
    def __init__(self, conf):
        dependency.Dependable.__init__(self)
        
        self.conf = conf
        
    def listTags(self):
        def _isTag(f):
            return not f.endswith('~') and ('.' not in f or
                                            '.' in f and f.split('.')[-1] != 'metadata')

        def _transformName(f):
            if f.endswith('.phantom'):
                return f.rsplit('.', 1)[0]
            return f

        def _listTags():
            try:
                return [_transformName(f)
                        for f in os.listdir(self.conf('tags.tags_directory'))
                        if _isTag(f)]
            except OSError:
                return []

        tags = _listTags()
        self.changed('list', tags)
        return defer.succeed(tags)
    
    def loadTag(self, tagName):
        def _loadTag():
            tagPath = _createTagPath(self.conf, tagName)
            if not os.path.exists(tagPath) and not os.path.exists(tagPath + '.phantom'):
                return defer.fail(TagNotFoundError(tagName))

            if os.path.exists(tagPath + '.phantom'):
                phantom = config.configFromStream(open(tagPath + '.phantom'), lazy=True)
            else:
                phantom = None

            if os.path.exists(tagPath + '.metadata'):
                metadata = json.loads(open(tagPath + '.metadata').read())
            else:
                metadata = {}

            if os.path.exists(tagPath):
                files = [f.rstrip('\n') for f in open(tagPath).readlines() if f.strip()]
            else:
                files = []

            return Tag(tagName=tagName,
                       files=files,
                       metadata=metadata,
                       phantom=phantom,
                       taskName=metadata.get('task_name'))

        # This is a really cheap trick to enusre any errors go through the deferred mechanism
        return defer.maybeDeferred(_loadTag).addCallback(lambda tag : self.changed('load', tag))

    
    def saveTag(self, tag):
        def _saveTag():
            tagPath = os.path.join(self.conf('tags.tags_directory'), tag.tagName)

            # We don't write phantom information now, we assume a human wrote it
            fout = open(tagPath, 'w')
            for f in tag.files:
                fout.write(f + '\n')
            fout.close()

            fout = open(tagPath + '.metadata', 'w')
            fout.write(json.dumps(tag.metadata, indent=True))
            fout.close()

            return tag

        tag = _saveTag()
        self.changed('save', tag)
        return defer.succeed(tag)

    @defer.inlineCallbacks
    def removeTag(self, tagName, deleteEverything=False):
        def _deleteFiles(files):
            for f in files:
                os.remove(f)

        def _deleteEmptyDirs(files):
            def _rmDir(d):
                return commands.runProcess(['rmdir', d],
                                           stderrf=log.err).addErrback(lambda _ : None)
            dirs = set([os.path.dirname(f) for f in files])
            return defer_utils.mapSerial(_rmDir, dirs)

        if deleteEverything:
            tag = yield loadTag(self.conf, tagName)
            yield threads.deferToThread(_deleteFiles, tag.files)
            yield _deleteEmptyDirs(files)

        tagPath = _createTagPath(self.conf, tagName)
        yield _deleteFiles([tagPath, tagPath + '.metadata'])
        self.changed('remove', tagName)
    

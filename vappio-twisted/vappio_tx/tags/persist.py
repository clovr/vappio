import os
import json

from twisted.python import log

from twisted.internet import threads
from twisted.internet import defer

from igs.utils import functional as func
from igs.utils import config as config

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

def listTags(conf):
    def _listTags():
        try:
            return [f
                    for f in os.listdir(conf('tags.tags_directory'))
                    if not f.endswith('~') and ('.' not in f or '.' in f and f.split('.')[-1] not in ['metadata', 'phantom'])]
        except IOError:
            return []
    return defer.maybeDeferred(_listTags)

def loadTag(conf, tagName):
    def _loadTag():
        tagPath = _createTagPath(conf, tagName)
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
    return defer.maybeDeferred(_loadTag)
                         

def saveTag(conf, tag):
    def _saveTag():
        tagPath = os.path.join(conf('tags.tags_directory'), tag.tagName)

        # We don't write phantom information now, we assume a human wrote it
        fout = open(tagPath, 'w')
        for f in tag.files:
            fout.write(f + '\n')
        fout.close()
    
        fout = open(tagPath + '.metadata', 'w')
        fout.write(json.dumps(tag.metadata, indent=True))
        fout.close()

        return tag

    return defer.maybeDeferred(_saveTag)

@defer.inlineCallbacks
def removeTag(conf, tagName, deleteEverything=False):
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
        tag = yield loadTag(conf, tagName)
        yield threads.deferToThread(_deleteFiles, tag.files)
        yield _deleteEmptyDirs(files)

    tagPath = _createTagPath(conf, tagName)
    yield _deleteFiles([tagPath, tagPath + '.metadata'])
    

import json

from igs.utils import logging

LOAD_TOPIC = '/topic/tags/load'
SAVE_TOPIC = '/topic/tags/save'
REMOVE_TOPIC = '/topic/tags/remove'

class TagNotify:
    def __init__(self, mq, persistManager):
        self.mq = mq
        self.persistManager = persistManager
        self.persistManager.addDependent(self)

    def update(self, who, aspect, value):
        if aspect == 'load':
            logging.debugPrint(lambda : 'TAG_NOTIFY: Sending LOAD ' + value.tagName)
            self.mq.send(LOAD_TOPIC, json.dumps(value.tagName))
        elif aspect == 'save':
            logging.debugPrint(lambda : 'TAG_NOTIFY: Sending SAVE ' + value.tagName)
            self.mq.send(SAVE_TOPIC, json.dumps(value.tagName))
        elif aspect == 'remove':
            logging.debugPrint(lambda : 'TAG_NOTIFY: Sending REMOVE ' + value)
            self.mq.send(REMOVE_TOPIC, json.dumps(value))

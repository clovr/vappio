from twisted.internet import defer


class LockManager:
    """
    Allows locks to be dynamically created and does simpel ref counting
    to clean up after them so we don't collect garbage.

    This is useful if you will be serializing many things based off a dynamic key.
    This ensures that if no work is being done for the key then the key does not
    exist in the list of keys, that way there is not a memory leak.
    """
    
    def __init__(self):
        self.locks = {}

    def run(self, key, f, *args, **kwargs):
        """
        key is an identifier that we want to index on in order to serialize
        functions through a DeferredLock.
        """
        
        keyLock = self.locks.setdefault(key,
                                        {'count': 0,
                                         'lock': defer.DeferredLock()})
        keyLock['count'] += 1
        return keyLock['lock'].run(self._runWrapper,
                                   key,
                                   f,
                                   *args,
                                   **kwargs)


    @defer.inlineCallbacks
    def _runWrapper(self, key, f, *args, **kwargs):
        def _cleanUp():
            keyLock = self.locks[key]
            keyLock['count'] -= 1
            if keyLock['count'] == 0:
                self.locks.pop(key)

        try:
            ret = yield f(*args, **kwargs)
            defer.returnValue(ret)
        finally:
            _cleanUp()
            

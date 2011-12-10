import time

from igs.utils import functional as func

class CacheEntry(func.Record):
    def __init__(self, val):
        func.Record.__init__(self, entryTime=time.time(), value=val)

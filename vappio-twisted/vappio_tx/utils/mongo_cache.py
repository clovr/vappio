#
# Implements a simple cache in mongo
import pymongo

from twisted.internet import threads

class Cache:
    def __init__(self, name, uniqF=None):
        self.name = name
        self.uniqF = uniqF

    def create(self):
        return threads.deferToThread(lambda : pymongo.Connection().clovr[self.name].remove())

    def query(self, criteria):
        return threads.deferToThread(lambda : list(pymongo.Connection().clovr[self.name].find(criteria)))

    def update(self, doc):
        doc = self.uniqF(doc) if self.uniqF else doc
        return threads.deferToThread(lambda : pymongo.Connection().clovr[self.name].save(doc, safe=True))

    save = update
    
    def remove(self, criteria):
        return threads.deferToThread(lambda : pymongo.Connection().clovr[self.name].remove(criteria))



def createCache(name, uniqF=None):
    cache = Cache(name, uniqF)
    return cache.create().addCallback(lambda _ : cache)

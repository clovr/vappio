import json

from twisted.internet import reactor
from twisted.internet import defer
from twisted.application import internet
from twisted.application import service
from twisted.web import resource
from twisted.web import server

from vappio_tx.mq import client
from vappio_tx.legacy import cgi as vappio_cgi
from vappio_tx.utils import queue

def TimeoutRequest():
    return json.dumps({'success': False,
                       'data': {'stacktrace': '',
                                'name': ''
                                'msg': 'Timed out waiting for response'}})
    
def MissingRequest():
    return json.dumps({'success': False,
                       'data': {'stacktrace': '',
                                'name': ''
                                'msg': 'Must pass request object'}})

class QueueRequest(resource.Resource):
    """Pushes work down a queue and returns the results"""

    def __init__(self, mq, name):
        self.mq = mq
        self.name = name
    
    def render_GET(self, request):
        if 'request' not in request.args:
            return MissingRequest()

        req = json.loads(request.args['request'][0])
        retQueue = queue.randomQueueName('www-data')
        newReq = {'payload': req,
                  'return_queue': retQueue}

        d = defer.Deferred()
        
        def _handleMsg(m):
            self.mq.unsubscribe(retQueue)
            d.callback(m.body)

        def _timeout():
            self.mq.unsubscribe(retQueue)
            d.errback()
            
        self.mq.subscribe(_handleMsg, retQueue)
        self.mq.send('/queue/' + self.name, json.dumps(newReq))
            
        reactor.callLater(TIMEOUT, _timeout)

        d.addCallback(request.write)

        def _error(_):
            request.write(TimeoutRequest())

        d.addErrback(_error)
        
        def _finish(_):
            request.finish()

        d.addCallback(_finish)
        
        return server.NOT_DONE_YET

class Root(resource.Resource):
    """Root resource"""

    def __init__(self, mq):
        self.mq = mq
        self.childFiles = []
    
    def putChild(self, name, resource):
        self.childFiles.append(name)
        resource.Resource.putChild(self, name, resource)
    
    def getChild(self, name, request):
        if name in self.childFiles:
            return resource.Resource.getChild(self, name, request)
        else:
            return QueueRequest(self.mq, name)

def makeService(conf):
    ms = service.MultiService()
    
    mqService = client.makeService(conf)
    root = Root(mqService)
    vappio_cgi.addCGIDir(root, conf('legacy.cgi_dir'), filterF=lambda f : f.endswith('.py'))

    mqService.addServiceParent(ms)
    internet.TCPServer(int(conf('www.port')), server.Site(root)).setServiceParent(ms)
    
    return ms


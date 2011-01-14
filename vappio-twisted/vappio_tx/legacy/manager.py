import json

from twisted.internet import reactor
from twisted.internet import defer
from twisted.application import internet
from twisted.application import service
from twisted.web import resource
from twisted.web import server
from twisted.python import log

from igs.utils import functional as func

from igs_tx.utils import http

from vappio_tx.mq import client
from vappio_tx.legacy import cgi as vappio_cgi
from vappio_tx.utils import queue
from vappio_tx import clusters

TIMEOUT = 60

def TimeoutRequestError():
    return json.dumps({'success': False,
                       'data': {'stacktrace': '',
                                'name': '',
                                'msg': 'Timed out waiting for response'}})
    
def MissingRequestError():
    return json.dumps({'success': False,
                       'data': {'stacktrace': '',
                                'name': '',
                                'msg': 'Must pass request object'}})

def UnknownError():
    return json.dumps({'success': False,
                       'data': {'stacktrace': '',
                                'name': '',
                                'msg': 'Unable to perform routing request'}})

class QueueRequest(resource.Resource):
    """Pushes work down a queue and returns the results"""

    isLeaf = True
    
    def __init__(self, mq, name):
        self.mq = mq
        self.name = name

        resource.Resource.__init__(self)
    
    def render_GET(self, request):
        if 'request' not in request.args or not request.args['request']:
            return MissingRequestError()

        req = json.loads(request.args['request'][0])
        retQueue = queue.randomQueueName('www-data')
        newReq = func.updateDict(req, dict(return_queue=retQueue,
                                           user_name='guest'))


        d = defer.Deferred()
        
        def _timeout():
            self.mq.unsubscribe(retQueue)
            d.errback(Exception('Waiting for request failed'))
            
        delayed = reactor.callLater(TIMEOUT, _timeout)
        
        def _handleMsg(mq, m):
            delayed.cancel()
            mq.unsubscribe(retQueue)
            d.callback(m.body)

        self.mq.subscribe(_handleMsg, retQueue)
        self.mq.send('/queue/' + self.name, json.dumps(newReq))
            

        d.addCallback(request.write)

        def _error(_):
            request.write(TimeoutRequestError())

        d.addErrback(_error)
        
        def _finish(_):
            request.finish()

        d.addCallback(_finish)
        
        return server.NOT_DONE_YET

    # Make them the same
    render_POST = render_GET

class Root(resource.Resource):
    """Root resource"""

    def __init__(self, mq):
        self.mq = mq
        self.childFiles = []

        resource.Resource.__init__(self)
    
    def putChild(self, name, r):
        self.childFiles.append(name)
        return resource.Resource.putChild(self, name, r)
    
    def getChild(self, name, request):
        if name in self.childFiles:
            return resource.Resource.getChild(self, name, request)
        else:
            return QueueRequest(self.mq, name)

def makeService(conf):
    ms = service.MultiService()
    
    mqService = client.makeService(conf)
    root = Root(mqService.mqFactory)
    vappio_cgi.addCGIDir(root, conf('legacy.cgi_dir'), filterF=lambda f : f.endswith('.py'))
    mqService.setServiceParent(ms)
    internet.TCPServer(int(conf('www.port')), server.Site(root)).setServiceParent(ms)
    
    return ms


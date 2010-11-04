from twisted.application import internet
from twisted.application import service
from twisted.internet import reactor
from twisted.web import resource
from twisted.web import server
from twisted.web import twcgi

class Root(resource.Resource):
    """Root resource"""


root = Root()
root.putChild('listProtocols_ws.py', twcgi.CGIScript('/var/www/vappio/listProtocols_ws.py'))

application = service.Application('www_data_components')
serviceCollection = service.IServiceCollection(application)

internet.TCPServer(8000, server.Site(root)).setServiceParent(serviceCollection)

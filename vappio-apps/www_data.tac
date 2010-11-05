from twisted.application import internet
from twisted.application import service
from twisted.internet import reactor
from twisted.web import resource
from twisted.web import server

from vappio_tw.legacy import cgi as vappio_cgi

class Root(resource.Resource):
    """Root resource"""


root = Root()
vappio_cgi.addCGIDir(root, '/var/www/vappio', filterF=lambda f : f.endswith('.py'))

application = service.Application('www_data_components')
serviceCollection = service.IServiceCollection(application)

internet.TCPServer(8000, server.Site(root)).setServiceParent(serviceCollection)

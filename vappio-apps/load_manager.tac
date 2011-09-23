from twisted.application import internet
from twisted.application import service
from twisted.internet import reactor

from igs.utils import logging

from vappio_tx import load_manager

from igs.utils import config

conf = config.configFromStream(open('/opt/vappio-apps/vappio_apps.conf'),
                               base=config.configFromEnv())

logging.DEBUG = conf('config.debug').lower() == 'true'

application = service.Application('www_data_components')
serviceCollection = service.IServiceCollection(application)

load_manager.makeService(conf).setServiceParent(serviceCollection)


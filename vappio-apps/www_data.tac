import pwd

from twisted.application import internet
from twisted.application import service
from twisted.internet import reactor

from igs.utils import logging

from vappio_tx import www_manager
from vappio_tx import tasklets_manager
from vappio_tx import credentials_manager
from vappio_tx import clusters_manager
from vappio_tx import pipelines_manager
from vappio_tx import tags_manager
from vappio_tx import tasks_manager
from vappio_tx import vm_manager

from igs.utils import config

conf = config.configFromStream(open('/opt/vappio-apps/vappio_apps.conf'),
                               base=config.configFromEnv())

logging.DEBUG = conf('config.debug').lower() == 'true'

user = pwd.getpwnam('www-data')

application = service.Application('www_data_components', uid=user.pw_uid, gid=user.pw_gid)
serviceCollection = service.IServiceCollection(application)


tasklets_manager.makeService(conf).setServiceParent(serviceCollection)
credentials_manager.makeService(conf).setServiceParent(serviceCollection)
clusters_manager.makeService(conf).setServiceParent(serviceCollection)
pipelines_manager.makeService(conf).setServiceParent(serviceCollection)
tags_manager.makeService(conf).setServiceParent(serviceCollection)
tasks_manager.makeService(conf).setServiceParent(serviceCollection)
vm_manager.makeService(conf).setServiceParent(serviceCollection)

www_manager.makeService(conf).setServiceParent(serviceCollection)

import pwd

from twisted.application import internet
from twisted.application import service
from twisted.internet import reactor

from vappio_tx.tasklets import manager as tasklets_manager
from vappio_tx.legacy import manager as www_manager

from igs.utils import config

conf = config.configFromMap({'mq.username': '',
                             'mq.password': '',
                             'mq.host': 'localhost',
                             'mq.port': 61613,
                             'tasklets.queue': '/queue/runMetrics_ws.py',
                             'tasklets.internal_queue': '/queue/run_tasklet',
                             'tasklets.concurrent_tasklets': 2,
                             'legacy.cgi_dir': '/var/www/vappio',
                             'www.port': 8000})



user = pwd.getpwnam('www-data')

application = service.Application('www_data_components', uid=user.pw_uid, gid=user.pw_gid)
serviceCollection = service.IServiceCollection(application)

tasklets_manager.makeService(conf).setServiceParent(serviceCollection)
www_manager.makeService(conf).setServiceParent(serviceCollection)



import pwd

from twisted.application import service

from vappio_tx.tasklets import manager

from igs.utils import config

conf = config.configFromMap({'mq.username': '',
                             'mq.password': '',
                             'mq.host': 'localhost',
                             'mq.port': 61613,
                             'tasklets.queue': '/queue/runTasklets_ws',
                             'tasklets.concurrent_tasklets': 2})


user = pwd.getpwnam('tasklets')

application = service.Application('tasklets_components', uid=user.pw_uid, gid=user.pw_gid)
serviceCollection = service.IServiceCollection(application)

manager.makeService(conf).setServiceParent(serviceCollection)

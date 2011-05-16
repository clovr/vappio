from igs.utils import functional as func

from igs.cgi.request import performQuery

LISTPROTOCOLS_URL = '/vappio/listProtocols_ws.py'
PROTOCOLCONFIG_URL = '/vappio/protocolConfig_ws.py'

def listProtocols(host, cluster):
    return performQuery(host, LISTPROTOCOLS_URL, dict(cluster=cluster))

def protocolConfig(host, cluster, protocolName):
    return performQuery(host, PROTOCOLCONFIG_URL, dict(cluster=cluster,
                                                       protocol=protocolName))



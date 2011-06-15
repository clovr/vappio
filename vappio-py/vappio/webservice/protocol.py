from igs.utils import functional as func

from igs.cgi.request import performQuery

LIST_URL = '/vappio/protocol_list'

def listProtocols(host, cluster):
    return performQuery(host, LIST_URL, dict(cluster=cluster))

def protocolConfig(host, cluster, protocolName):
    return performQuery(host, LIST_URL, dict(cluster=cluster,
                                             criteria={'protocol': protocolName},
                                             detail=True))



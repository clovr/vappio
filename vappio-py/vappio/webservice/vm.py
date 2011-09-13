from igs.cgi.request import performQuery

INFO_URL = '/vappio/vm_info'

def info():
    return performQuery('localhost', INFO_URL, {})

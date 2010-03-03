##
# Web services dealing with files such as uploading and tagging

from igs.cgi.request import performQuery

TAGDATA_URL = '/vappio/tagData_ws.py'
UPLOADTAG_URL = '/vappio/uploadTag_ws.py'
QUERYTAG_URL = '/vappio/queryTag_ws.py'

def tagData(host, name, tagName, files, recursive, expand, append, overwrite):
    performQuery(host, TAGDATA_URL, dict(name=name,
                                         tag_name=tagName,
                                         files=files,
                                         recursive=recursive,
                                         expand=expand,
                                         append=append,
                                         overwrite=overwrite))


def uploadTag(host, name, tagName, srcCluster, dstCluster, expand):
    performQuery(host, UPLOADTAG_URL, dict(name=name,
                                           tag_name=tagName,
                                           src_cluster=srcCluster,
                                           dst_cluster=dstCluster,
                                           expand=expand))
    

def queryTag(host, name, tagName):
    return performQuery(host, QUERYTAG_URL, dict(name=name, tag_name=tagName))

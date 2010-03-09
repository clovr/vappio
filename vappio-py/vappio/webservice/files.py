##
# Web services dealing with files such as uploading and tagging

from igs.utils.config import configFromMap
from igs.cgi.request import performQuery

TAGDATA_URL = '/vappio/tagData_ws.py'
UPLOADTAG_URL = '/vappio/uploadTag_ws.py'
DOWNLOADTAG_URL = '/vappio/downloadTag_ws.py'
QUERYTAG_URL = '/vappio/queryTag_ws.py'

def tagData(host, name, tagName, files, recursive, expand, append, overwrite):
    return performQuery(host, TAGDATA_URL, dict(name=name,
                                                tag_name=tagName,
                                                files=files,
                                                recursive=recursive,
                                                expand=expand,
                                                append=append,
                                                overwrite=overwrite))


def uploadTag(host, tagName, srcCluster, dstCluster, expand, tagBaseDir):
    return performQuery(host, UPLOADTAG_URL, dict(tag_name=tagName,
                                                  src_cluster=srcCluster,
                                                  dst_cluster=dstCluster,
                                                  expand=expand,
                                                  tag_base_dir=tagBaseDir))
    

def downloadTag(host, tagName, srcCluster, dstCluster, expand):
    return performQuery(host, DOWNLOADTAG_URL, dict(tag_name=tagName,
                                                    src_cluster=srcCluster,
                                                    dst_cluster=dstCluster,
                                                    expand=expand))
    


def queryTag(host, name, tagName):
    return configFromMap(performQuery(host, QUERYTAG_URL, dict(name=name, tag_name=tagName)))


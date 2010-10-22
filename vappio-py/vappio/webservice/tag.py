##
# Web services dealing with files such as uploading and tagging

from igs.utils.config import configFromMap
from igs.cgi.request import performQuery

TAGDATA_URL = '/vappio/tagData_ws.py'
UPLOADTAG_URL = '/vappio/uploadTag_ws.py'
DOWNLOADTAG_URL = '/vappio/downloadTag_ws.py'
QUERYTAG_URL = '/vappio/queryTag_ws.py'
REALIZEPHANTOM_URL = '/vappio/realizePhantom_ws.py'

def tagData(host, name, tagName, tagBaseDir, files, recursive, expand, compress, append, overwrite, metadata):
    return performQuery(host, TAGDATA_URL, dict(name=name,
                                                tag_name=tagName,
                                                tag_base_dir=tagBaseDir,
                                                files=files,
                                                recursive=recursive,
                                                expand=expand,
                                                compress=compress,
                                                append=append,
                                                overwrite=overwrite,
                                                tag_metadata=metadata))


def uploadTag(host, tagName, srcCluster, dstCluster, expand, compress):
    return performQuery(host, UPLOADTAG_URL, dict(tag_name=tagName,
                                                  src_cluster=srcCluster,
                                                  dst_cluster=dstCluster,
                                                  expand=expand,
                                                  compress=compress))
    

def downloadTag(host, tagName, srcCluster, dstCluster, outputDir, expand, compress):
    return performQuery(host, DOWNLOADTAG_URL, dict(tag_name=tagName,
                                                    src_cluster=srcCluster,
                                                    dst_cluster=dstCluster,
                                                    output_dir=outputDir,
                                                    expand=expand,
                                                    compress=compress))
    


def listAllTags(host, name):
    """
    Returns a list of all tags on a machine
    """
    return dict([(t['name'], configFromMap(t, lazy=True)) for t in performQuery(host, QUERYTAG_URL, dict(name=name))])
    
def queryTag(host, name, tagName):
    ##
    # A tag may contain some keys that shouldn't be evaluated
    return configFromMap(performQuery(host, QUERYTAG_URL, dict(name=name, tag_name=tagName))[0], lazy=True)

def realizePhantom(host, name, tagName):
    return performQuery(host, REALIZEPHANTOM_URL, dict(name=name, tag_name=tagName))

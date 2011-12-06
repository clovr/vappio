##
# Web services dealing with files such as uploading and tagging

from igs.utils.config import configFromMap
from igs.cgi.request import performQuery

CREATEUPDATE_URL = '/vappio/tag_createupdate'
TRANSFER_URL = '/vappio/tag_transfer'
LIST_URL = '/vappio/tag_list'
DELETE_URL = '/vappio/tag_delete'

def tagData(host,
            cluster,
            action,
            tagName,
            files,
            urls,
            metadata,
            recursive,
            expand,
            compressDir):
    return performQuery(host, CREATEUPDATE_URL, dict(cluster=cluster,
                                                     action=action,
                                                     tag_name=tagName,
                                                     files=files,
                                                     urls=urls,
                                                     metadata=metadata,
                                                     recursive=recursive,
                                                     expand=expand,
                                                     compress_dir=compressDir))


def transferTag(host, cluster, tagName, srcCluster, dstCluster, compress=False):
    return performQuery(host, TRANSFER_URL, dict(cluster=cluster,
                                                 tag_name=tagName,
                                                 src_cluster=srcCluster,
                                                 dst_cluster=dstCluster,
                                                 compress=compress))
    

def listTags(host, cluster, criteria, detail):
    """
    Returns a list of all tags on a machine
    """
    return performQuery(host, LIST_URL, dict(cluster=cluster,
                                             criteria=criteria,
                                             detail=detail))

def deleteTag(host, cluster, tagName, deleteEverything):
    return performQuery(host, DELETE_URL, dict(cluster=cluster,
                                               tag_name=tagName,
                                               delete_everything=deleteEverything))

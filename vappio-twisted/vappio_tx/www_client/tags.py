from igs_tx.utils import http

from vappio_tx.tags import persist

CREATEUPDATE_URL = '/vappio/tag_createupdate'
DELETE_URL = '/vappio/tag_delete'
LIST_URL = '/vappio/tag_list'
TRANSFER_URL = '/vappio/tag_transfer'
REALIZE_URL = '/vappio/tag_realize'

def loadTagsBy(host, clusterName, userName, criteria, detail):
    return http.performQuery(host,
                             LIST_URL,
                             dict(cluster=clusterName,
                                  user_name=userName,
                                  criteria=criteria,
                                  detail=detail))

def loadTag(host, clusterName, userName, tagName):
    def _failIfNoTag(tags):
        if not tags or len(tags) > 1:
            raise persist.TagNotFoundError(tagName)
        else:
            return tags[0]
    return http.performQuery(host,
                             LIST_URL,
                             dict(cluster=clusterName,
                                  user_name=userName,
                                  criteria={'tag_name': tagName},
                                  detail=True)).addCallback(_failIfNoTag)


def tagData(host,
            clusterName,
            userName,
            action,
            tagName,
            files,
            metadata,
            recursive,
            expand,
            compressDir,
            urls=[],
            timeout=30,
            tries=4):
    return http.performQuery(host,
                             CREATEUPDATE_URL,
                             dict(cluster=clusterName,
                                  user_name=userName,
                                  tag_name=tagName,
                                  action=action,
                                  files=files,
                                  metadata=metadata,
                                  recursive=recursive,
                                  expand=expand,
                                  compress_dir=compressDir,
                                  urls=urls),
                             timeout=timeout,
                             tries=tries)

def realizePhantom(host,
                   clusterName,
                   userName,
                   tagName,
                   phantom,
                   metadata,
                   timeout=30,
                   tries=4):
    return http.performQuery(host,
                             REALIZE_URL,
                             dict(cluster=clusterName,
                                  user_name=userName,
                                  tag_name=tagName,
                                  phantom=phantom,
                                  metadata=metadata),
                             timeout=timeout,
                             tries=tries)    

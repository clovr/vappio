##
# Web services dealing with files such as uploading and tagging

from igs.cgi.request import performQuery

TAGDATA_URL = '/vappio/tagData_ws.py'

def tagData(host, name, tagName, files, recursive, expand, append, overwrite):
    performQuery(host, TAGDATA_URL, dict(name=name,
                                         tag_name=tagName,
                                         files=files,
                                         recursive=recursive,
                                         expand=expand,
                                         append=append,
                                         overwrite=overwrite))
    

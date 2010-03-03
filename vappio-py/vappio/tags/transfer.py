##
# Transfering tags to/from a machine
import os

from igs.utils.ssh import scpToEx
from igs.utils.logging import errorPrintS

from vappio.tags.tagfile import loadTagFile

from vappio.instance.control import runSystemInstanceEx

def makePathRelative(path):
    if path[0] == '/':
        return path[1:]
    else:
        return path

def uploadTag(srcCluster, dstCluster, tagName, tagDir=None):
    """
    srcCluster - Source cluster - currently this needs to be 'local'
    dstCluster - Destination cluster
    tagName - The tag to be copied, will have the same name on the destination cluster,
              must exist on srcCluster
    tagDir - the local base directory in the tag files, this will be removed from the beginning of
             each tag file if present.  Default sto srcCluster.config('dirs.tag_dir')

    Tags are upload into dstCluster.config('dirs.upload_dir')

    This returns a list of file names that were uploaded
    """
    tagData = loadTagFile(os.path.join(srcCluster.config('dirs.tag_dir'), tagName))

    ##
    # First step is to create a list of directorys that we should make on
    # the destination cluster.  We also want to strip off our local dirs.tag_dir
    # from the dir names and add teh dstCluster's
    dirNames = set([os.path.join(dstCluster.config('dirs.upload_dir'), tagName,
                                 makePathRelative(os.path.dirname(f).replace(srcCluster.config('dirs.tag_dir'), '')))
                    for f in tagData('files')])

    ##
    # Next we want to take the list of local files, remove the dirs.tag_dir and replace it
    # with the destination clusters.  We maek a list of tuples so we know the local file
    # and destinatio file name which we will then loop over and upload
    dstFileNames = [(f, os.path.join(dstCluster.config('dirs.upload_dir'), tagName,
                                     makePathRelative(f.replace(srcCluster.config('dirs.tag_dir'), ''))))
                    for f in tagData('files')]

    ##
    # Next, lets call 'mkdir -p' on all the dirs we need to make on the destination cluster
    for d in dirNames:
        runSystemInstanceEx(dstCluster.master,
                            'mkdir -p ' + d,
                            None,
                            errorPrintS,
                            user=srcCluster.config('ssh.user'),
                            options=srcCluster.config('ssh.options'),
                            log=True)

    ##
    # Now, copy up all of the files
    for l, d in dstFileNames:
        scpToEx(dstCluster.master.publicDNS, l, d, user=srcCluster.config('ssh.user'), options=srcCluster.config('ssh.options'), log=True)

    ##
    # return the list of uploaded filenames
    return [d for l, d in dstFileNames]

    
